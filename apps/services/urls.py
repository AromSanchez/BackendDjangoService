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
    
    # Categorías públicas
    path('categories/', views.categories_list, name='categories_list'),
    
    # Admin - Gestión de categorías
    path('admin/categories/', views.admin_categories_list_create, name='admin_categories_list_create'),
    path('admin/categories/<int:category_id>/', views.admin_category_detail, name='admin_category_detail'),
    path('admin/categories/<int:category_id>/toggle-status/', views.admin_category_toggle_status, name='admin_category_toggle_status'),
]

