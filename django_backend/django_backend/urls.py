from django.contrib import admin
from django.urls import path
from pollution import views
from pollution.views import login_view

urlpatterns = [
    path('', views.home),
    path('admin/', admin.site.urls),

    # ===== AUTH =====
    path('api/login/', login_view),
    path('api/register/', views.register),
    path('api/reset-password/', views.reset_password),  # ✅ keep (we'll define it)

    # ===== DATA =====
    path('api/data/', views.get_pollution_data),
    path('save/', views.save_data),

    # ===== CORE =====
    path('pollution/', views.pollution),

    # ===== ML =====
    path('api/predict/', views.predict_api),

    # ===== ANALYTICS =====
    path('analytics_data/', views.analytics_data),

    # ===== EXTRA =====
    path('tiles/', views.tiles),
    path('history/', views.history),
    path('dashboard/', views.dashboard),
    path('api/login/', login_view),
    path('api/register/', views.register),
    path('api/reset-password/', views.reset_password),
]