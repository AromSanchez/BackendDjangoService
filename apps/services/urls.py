"""
URLs para el módulo de servicios
"""
from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Servicios del proveedor (CRUD protegido)
    path('', views.services_list_create, name='services_list_create'),
    path('<int:service_id>/', views.service_detail, name='service_detail'),
    
    # Servicios públicos (para clientes)
    path('public/', views.services_public_list, name='services_public_list'),
    
    # Categorías
    path('categories/', views.categories_list, name='categories_list'),
]
