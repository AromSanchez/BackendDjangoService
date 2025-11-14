"""
URLs para el módulo Dashboard
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Endpoint principal del dashboard (protegido)
    path('', views.dashboard_view, name='dashboard'),
    
    # Endpoint del perfil del usuario (protegido)
    path('profile/', views.user_profile_view, name='profile'),
    
    # Estadísticas avanzadas por rol
    path('stats/provider/', views.provider_stats, name='provider_stats'),
    path('stats/customer/', views.customer_stats, name='customer_stats'),
    path('stats/admin/', views.admin_stats, name='admin_stats'),
]
