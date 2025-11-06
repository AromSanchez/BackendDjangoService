"""
URLs para las vistas de autenticación JWT
"""
from django.urls import path
from . import views

urlpatterns = [
    # Vista protegida Django estándar
    path('protected/', views.protected_view, name='protected'),
    
    # Vistas protegidas Django REST Framework
    path('protected-drf/', views.protected_view_drf, name='protected-drf'),
    path('user-info/', views.user_info, name='user-info'),
    
    # Vista pública
    path('public/', views.public_view, name='public'),
]
