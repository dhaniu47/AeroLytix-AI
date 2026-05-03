from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('analytics_data/', views.analytics_data),
]