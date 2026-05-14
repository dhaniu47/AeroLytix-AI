from django.contrib import admin
from django.urls import path
from pollution import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # HOME
    path('', views.index, name='index'),

    # AUTH
    path('api/login/', views.login_view),
    path('api/register/', views.register),
    path('api/reset-password/', views.reset_password),

    # DATA
    path('api/data/', views.get_pollution_data),
    path('save/', views.save_data),

    # CORE
    path('pollution/', views.pollution),

    # ML
    path('api/predict/', views.predict_api),

    # ANALYTICS
    path('analytics_data/', views.analytics_data),

    # EXTRA
    path('tiles/', views.tiles),
    path('history/', views.history),
    path('dashboard/', views.dashboard),
]