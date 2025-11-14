"""
URLs para el módulo de reports
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # CRUD básico de reports
    path('', views.reports_list_create, name='reports_list_create'),
    path('<int:report_id>/', views.report_detail, name='report_detail'),
    
    # Admin endpoints
    path('admin/', views.admin_reports_list, name='admin_reports_list'),
    path('admin/<int:report_id>/', views.admin_report_update, name='admin_report_update'),
    path('admin/<int:report_id>/resolve/', views.admin_report_resolve, name='admin_report_resolve'),
    path('admin/stats/', views.admin_reports_stats, name='admin_reports_stats'),
]
