from django.http import JsonResponse
from airsat.pollution.models import PollutionData

def home(request):
    return JsonResponse({"status": "API working"})

def analytics_data(request):
    data = PollutionData.objects.all()

    if not data.exists():
        return JsonResponse({"average": 0, "max": 0})

    avg = sum([d.no2 for d in data]) / len(data)
    max_val = max([d.no2 for d in data])

    return JsonResponse({
        "average": round(avg, 2),
        "max": max_val
    })