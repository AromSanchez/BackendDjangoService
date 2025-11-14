"""
URLs para el módulo de bookings
"""
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # CRUD básico de bookings
    path('', views.bookings_list_create, name='bookings_list_create'),
    path('<int:booking_id>/', views.booking_detail, name='booking_detail'),
    
    # Acciones específicas de bookings
    path('<int:booking_id>/accept/', views.booking_accept, name='booking_accept'),
    path('<int:booking_id>/reject/', views.booking_reject, name='booking_reject'),
    path('<int:booking_id>/start/', views.booking_start, name='booking_start'),
    path('<int:booking_id>/complete/', views.booking_complete, name='booking_complete'),
    path('<int:booking_id>/cancel/', views.booking_cancel, name='booking_cancel'),
    
    # Estadísticas
    path('stats/', views.bookings_stats, name='bookings_stats'),
]
