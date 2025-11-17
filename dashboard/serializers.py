"""
Serializers para el módulo Dashboard
"""
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo User
    Excluye el password por seguridad
    """
    role_display = serializers.CharField(source='get_role_display_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'email',
            'phone_number',
            'phone_verified_at',
            'role',
            'role_display',
            'is_active',
            'provider_status',
            'created_at'
        ]
        # Excluir password por seguridad


class DashboardDataSerializer(serializers.Serializer):
    """
    Serializer para la respuesta del dashboard
    """
    role = serializers.CharField()
    user = UserSerializer()
    data = serializers.DictField()
    message = serializers.CharField(required=False)


class DashboardStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas del dashboard
    """
    # Estadísticas generales
    total_services = serializers.IntegerField(default=0)
    total_bookings = serializers.IntegerField(default=0)
    total_reviews = serializers.IntegerField(default=0)
    total_users = serializers.IntegerField(default=0)
    
    # Estadísticas por período
    this_month_bookings = serializers.IntegerField(default=0)
    this_month_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Ratings
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Tendencias
    bookings_trend = serializers.ListField(child=serializers.DictField(), default=list)
    revenue_trend = serializers.ListField(child=serializers.DictField(), default=list)


class ProviderStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de proveedor
    """
    # Servicios
    total_services = serializers.IntegerField(default=0)
    active_services = serializers.IntegerField(default=0)
    published_services = serializers.IntegerField(default=0)
    
    # Bookings
    total_bookings = serializers.IntegerField(default=0)
    pending_bookings = serializers.IntegerField(default=0)
    completed_bookings = serializers.IntegerField(default=0)
    
    # Reviews y rating
    total_reviews = serializers.IntegerField(default=0)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Ingresos
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    this_month_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Tendencias
    bookings_by_month = serializers.ListField(child=serializers.DictField(), default=list)
    revenue_by_month = serializers.ListField(child=serializers.DictField(), default=list)


class CustomerStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de cliente
    """
    # Bookings
    total_bookings = serializers.IntegerField(default=0)
    pending_bookings = serializers.IntegerField(default=0)
    completed_bookings = serializers.IntegerField(default=0)
    
    # Reviews
    total_reviews = serializers.IntegerField(default=0)
    
    # Favoritos
    total_favorites = serializers.IntegerField(default=0)
    
    # Gastos
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    this_month_spent = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Servicios más utilizados
    top_categories = serializers.ListField(child=serializers.DictField(), default=list)
    recent_bookings = serializers.ListField(child=serializers.DictField(), default=list)


class AdminStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de administrador
    """
    # Usuarios
    total_users = serializers.IntegerField(default=0)
    total_customers = serializers.IntegerField(default=0)
    total_providers = serializers.IntegerField(default=0)
    pending_providers = serializers.IntegerField(default=0)
    
    # Servicios
    total_services = serializers.IntegerField(default=0)
    published_services = serializers.IntegerField(default=0)
    pending_services = serializers.IntegerField(default=0)
    
    # Bookings
    total_bookings = serializers.IntegerField(default=0)
    completed_bookings = serializers.IntegerField(default=0)
    
    # Reviews y reportes
    total_reviews = serializers.IntegerField(default=0)
    flagged_reviews = serializers.IntegerField(default=0)
    open_reports = serializers.IntegerField(default=0)
    
    # Ingresos de la plataforma
    platform_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Tendencias
    users_growth = serializers.ListField(child=serializers.DictField(), default=list)
    bookings_growth = serializers.ListField(child=serializers.DictField(), default=list)
    revenue_growth = serializers.ListField(child=serializers.DictField(), default=list)
    services_growth = serializers.ListField(child=serializers.DictField(), default=list)
    users_trend = serializers.FloatField(default=0)
    services_trend = serializers.FloatField(default=0)
    revenue_trend = serializers.FloatField(default=0)
