import json
import pandas as pd
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Avg, Max
from django.core.cache import cache

from .models import PollutionData
from sklearn.linear_model import LinearRegression

# 🔐 YOUR API KEY
API_KEY = "59f94b454a8b55e8d55f552b6dda2e46"


# =========================
# AQI LEVEL
# =========================
def get_level(aqi):
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy (Sensitive)"
    elif aqi <= 200:
        return "Unhealthy"
    else:
        return "Hazardous"


# =========================
# HOME
# =========================
def home(request):
    return render(request, "index.html")


# =========================
# LOGIN
# =========================
@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)

    user = authenticate(
        request,
        username=data.get("username"),
        password=data.get("password")
    )

    if user:
        login(request, user)
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "failed"})


# =========================
# REGISTER
# =========================
@csrf_exempt
def register(request):
    data = json.loads(request.body)

    if User.objects.filter(username=data.get("username")).exists():
        return JsonResponse({"status": "exists"})

    User.objects.create_user(
        username=data.get("username"),
        password=data.get("password")
    )

    return JsonResponse({"status": "created"})


# =========================
# RESET PASSWORD
# =========================
@csrf_exempt
def reset_password(request):
    data = json.loads(request.body)

    user = User.objects.filter(username=data.get("username")).first()

    if not user:
        return JsonResponse({"status": "not_found"})

    user.set_password(data.get("new_password"))
    user.save()

    return JsonResponse({"status": "updated"})


# =========================
# 🔥 REAL-TIME POLLUTION (FIXED)
# =========================
def pollution(request):

    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if not lat or not lon:
        return JsonResponse({"error": "lat/lon required"}, status=400)

    lat = float(lat)
    lon = float(lon)

    # 🔥 CACHE (avoid API spam)
    cache_key = f"aqi_{round(lat,2)}_{round(lon,2)}"
    cached = cache.get(cache_key)

    if cached:
        return JsonResponse(cached)

    try:
        # ===== OPENWEATHER AQI =====
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        res = requests.get(url).json()

        aqi_index = res["list"][0]["main"]["aqi"]

        # convert 1–5 → real AQI
        mapping = {1: 40, 2: 80, 3: 120, 4: 180, 5: 250}
        aqi = mapping.get(aqi_index, 100)

        # ===== CITY NAME =====
        geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={API_KEY}"
        geo = requests.get(geo_url).json()

        city = geo[0]["name"] if geo else "Unknown"

        result = {
            "aqi": aqi,
            "level": get_level(aqi),
            "city": city
        }

        # 🔥 SAVE HISTORY (REAL DATA)
        PollutionData.objects.create(
            lat=lat,
            lon=lon,
            no2=aqi,
            pm25=aqi,
            city=city,
            level=get_level(aqi)
        )

        # 🔥 CACHE FOR 2 MIN
        cache.set(cache_key, result, timeout=120)

        return JsonResponse(result)

    except Exception as e:
        print("API ERROR:", e)
        return JsonResponse({"error": "API failed"})


# =========================
# HEATMAP DATA (REAL)
# =========================
def get_pollution_data(request):

    data = PollutionData.objects.order_by("-created_at")[:300]

    result = [
        {"lat": d.lat, "lon": d.lon, "no2": d.no2}
        for d in data
    ]

    return JsonResponse({"data": result})


# =========================
# 🔥 SMART ML PREDICTION
# =========================
def predict_future():

    data = PollutionData.objects.order_by("created_at")[:200]

    if len(data) < 10:
        return 80

    df = pd.DataFrame(list(data.values("pm25")))
    df["time"] = range(len(df))

    X = df[["time"]]
    y = df["pm25"].fillna(0)

    model = LinearRegression()
    model.fit(X, y)

    pred = model.predict([[len(df) + 10]])[0]

    return max(0, round(pred, 2))


@csrf_exempt
def predict_api(request):
    return JsonResponse({"prediction": predict_future()})


# =========================
# ANALYTICS
# =========================
def analytics_data(request):
    data = PollutionData.objects.all()

    return JsonResponse({
        "avg": data.aggregate(Avg("no2"))["no2__avg"] or 0,
        "max": data.aggregate(Max("no2"))["no2__max"] or 0
    })


# =========================
# EXTRA SAFE
# =========================
def save_data(request):
    return JsonResponse({"message": "ok"})


def tiles(request):
    return JsonResponse({"message": "ok"})


def history(request):
    return JsonResponse({"message": "ok"})


def dashboard(request):
    return JsonResponse({"message": "ok"})