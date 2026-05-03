from django.db import models
from django.contrib.auth.models import User

class PollutionData(models.Model):
    lat = models.FloatField()
    lon = models.FloatField()

    no2 = models.FloatField()
    pm25 = models.FloatField(null=True, blank=True)

    city = models.CharField(max_length=100, null=True, blank=True)

    level = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city} ({self.lat}, {self.lon}) - {self.level}"


class SavedLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lat = models.FloatField()
    lon = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.lat}, {self.lon}"