"""
URL configuration for conectaya project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.services.provider_profile_view import provider_public_profile

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API de autenticación (ejemplos JWT)
    path('api/auth/', include('conectaya.authentication.urls')),
    
    # API pública de proveedores (sin autenticación)
    path('api/providers/<int:provider_id>/profile/', provider_public_profile, name='provider-public-profile'),
    
    # API del dashboard principal (protegido)
    path('api/dashboard/', include('dashboard.urls')),
    
    # APIs de las apps del marketplace
    path('api/dashboard/services/', include('apps.services.urls')),
    path('api/dashboard/bookings/', include('apps.bookings.urls')),
    path('api/dashboard/reviews/', include('apps.reviews.urls')),
    path('api/dashboard/favorites/', include('apps.favorites.urls')),
    path('api/dashboard/reports/', include('apps.reports.urls')),
    path('api/dashboard/chat/', include('apps.chat.urls')),
    path('api/dashboard/users/', include('apps.users.urls')),
    path('api/', include('apps.notifications.urls')),  # 🔥 Notifications
]
