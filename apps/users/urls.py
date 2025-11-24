"""
URLs para el módulo de users
"""
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Perfil del usuario
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/<int:user_id>/', views.user_profile_public, name='user_profile_public'),
    path('info/', views.user_info, name='user_info'),
    
    # Funcionalidades adicionales de perfil
    path('avatar/', views.user_upload_avatar, name='user_upload_avatar'),
    path('notifications/', views.user_update_notifications, name='user_update_notifications'),
    path('activity/', views.user_activity_summary, name='user_activity_summary'),
    path('update-name/', views.update_full_name, name='update_full_name'),
    path('update-password/', views.update_password, name='update_password'),
    
    # Admin endpoints
    path('admin/', views.admin_users_list, name='admin_users_list'),
    path('admin/<int:target_user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/<int:target_user_id>/toggle/', views.admin_user_toggle_status, name='admin_user_toggle_status'),
    path('admin/stats/', views.admin_users_stats, name='admin_users_stats'),
]
