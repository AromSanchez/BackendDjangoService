"""
URLs para el módulo de favorites
"""
from django.urls import path
from . import views

app_name = 'favorites'

urlpatterns = [
    # CRUD básico de favorites
    path('', views.favorites_list_create, name='favorites_list_create'),
    path('remove/<int:service_id>/', views.favorite_remove, name='favorite_remove'),
    
    # Utilidades
    path('check/<int:service_id>/', views.favorite_check, name='favorite_check'),
    path('toggle/<int:service_id>/', views.favorite_toggle, name='favorite_toggle'),
    path('stats/', views.favorites_stats, name='favorites_stats'),
]
