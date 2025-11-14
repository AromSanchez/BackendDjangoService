"""
URLs para el módulo de reviews
"""
from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # CRUD básico de reviews
    path('', views.reviews_list_create, name='reviews_list_create'),
    path('<int:review_id>/', views.review_detail, name='review_detail'),
    
    # Reviews por servicio (público)
    path('service/<int:service_id>/', views.service_reviews, name='service_reviews'),
    
    # Reportar review
    path('<int:review_id>/flag/', views.review_flag, name='review_flag'),
    
    # Admin endpoints
    path('admin/', views.admin_reviews_list, name='admin_reviews_list'),
    path('admin/<int:review_id>/', views.admin_review_moderate, name='admin_review_moderate'),
]
