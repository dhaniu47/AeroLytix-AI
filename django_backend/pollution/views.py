import json
import os
from functools import wraps

import pandas as pd
import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import Avg, Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from sklearn.linear_model import LinearRegression

from .models import PollutionData


OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")


def api_login_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapped


def parse_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None


def get_level(aqi):
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy (Sensitive)"
    if aqi <= 200:
        return "Unhealthy"
    return "Hazardous"


@ensure_csrf_cookie
def index(request):
    return render(request, "index.html")


@require_POST
def login_view(request):
    data = parse_json(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = str(data.get("username", "")).strip()
    password = data.get("password", "")

    if not username or not password:
        return JsonResponse({"error": "Username and password are required"}, status=400)

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse({"status": "failed"}, status=401)

    login(request, user)
    return JsonResponse({"status": "success", "username": user.username})


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"status": "logged_out"})


@require_POST
def register(request):
    data = parse_json(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = str(data.get("username", "")).strip()
    password = data.get("password", "")

    if not username or not password:
        return JsonResponse({"error": "Username and password are required"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"status": "exists"}, status=409)

    user = User(username=username)

    try:
        validate_password(password, user)
    except ValidationError as exc:
        return JsonResponse({"error": exc.messages}, status=400)

    user.set_password(password)
    user.save()

    return JsonResponse({"status": "created"}, status=201)


@api_login_required
@require_POST
def reset_password(request):
    data = parse_json(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return JsonResponse(
            {"error": "Current password and new password are required"},
            status=400,
        )

    if not request.user.check_password(current_password):
        return JsonResponse({"error": "Current password is incorrect"}, status=400)

    try:
        validate_password(new_password, request.user)
    except ValidationError as exc:
        return JsonResponse({"error": exc.messages}, status=400)

    request.user.set_password(new_password)
    request.user.save()
    logout(request)

    return JsonResponse({"status": "updated"})


@api_login_required
@require_GET
def pollution(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if not lat or not lon:
        return JsonResponse({"error": "lat/lon required"}, status=400)

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return JsonResponse({"error": "lat/lon must be numeric"}, status=400)

    if not OPENWEATHER_API_KEY:
        return JsonResponse({"error": "OpenWeather API key is not configured"}, status=503)

    cache_key = f"aqi_{round(lat, 2)}_{round(lon, 2)}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    try:
        url = (
            "https://api.openweathermap.org/data/2.5/air_pollution"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
        )
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        payload = res.json()

        aqi_index = payload["list"][0]["main"]["aqi"]
        mapping = {1: 40, 2: 80, 3: 120, 4: 180, 5: 250}
        aqi = mapping.get(aqi_index, 100)

        geo_url = (
            "https://api.openweathermap.org/geo/1.0/reverse"
            f"?lat={lat}&lon={lon}&limit=1&appid={OPENWEATHER_API_KEY}"
        )
        geo_res = requests.get(geo_url, timeout=10)
        geo_res.raise_for_status()
        geo = geo_res.json()
        city = geo[0]["name"] if geo else "Unknown"

        result = {
            "aqi": aqi,
            "level": get_level(aqi),
            "city": city,
        }

        PollutionData.objects.create(
            lat=lat,
            lon=lon,
            no2=aqi,
            pm25=aqi,
            city=city,
            level=get_level(aqi),
        )

        cache.set(cache_key, result, timeout=120)
        return JsonResponse(result)

    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return JsonResponse({"error": "AQI service failed"}, status=502)


@api_login_required
@require_GET
def get_pollution_data(request):
    data = PollutionData.objects.order_by("-created_at")[:300]
    result = [
        {"lat": d.lat, "lon": d.lon, "no2": d.no2}
        for d in data
    ]
    return JsonResponse({"data": result})


def predict_future():
    data = PollutionData.objects.order_by("created_at")[:200]

    if len(data) < 10:
        return 80

    df = pd.DataFrame(list(data.values("pm25")))
    df["time"] = range(len(df))

    model = LinearRegression()
    model.fit(df[["time"]], df["pm25"].fillna(0))

    prediction = model.predict([[len(df) + 10]])[0]
    return max(0, round(prediction, 2))


@api_login_required
@require_GET
def predict_api(request):
    return JsonResponse({"prediction": predict_future()})


@api_login_required
@require_GET
def analytics_data(request):
    data = PollutionData.objects.all()
    return JsonResponse(
        {
            "avg": data.aggregate(Avg("no2"))["no2__avg"] or 0,
            "max": data.aggregate(Max("no2"))["no2__max"] or 0,
        }
    )


@api_login_required
@require_POST
def save_data(request):
    return JsonResponse({"message": "ok"})


@api_login_required
@require_GET
def tiles(request):
    return JsonResponse({"message": "ok"})


@api_login_required
@require_GET
def history(request):
    return JsonResponse({"message": "ok"})


@api_login_required
@require_GET
def dashboard(request):
    return JsonResponse({"message": "ok"})
