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
]
