"""
Serializers para el módulo de favorites
"""
from rest_framework import serializers
from .models import Favorite
from apps.services.serializers import ServiceListSerializer
from apps.services.models import Service


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer completo para favorites"""
    
    service = ServiceListSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'user_id', 'service', 'created_at']
        read_only_fields = ['id', 'user_id', 'created_at']


class FavoriteCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear favorites"""
    
    class Meta:
        model = Favorite
        fields = ['service']
    
    def validate_service(self, value):
        """Validar que el servicio existe y está activo"""
        if not value.is_active or not value.is_published:
            raise serializers.ValidationError("El servicio no está disponible")
        return value
    
    def create(self, validated_data):
        """Crear un nuevo favorite"""
        return Favorite.objects.create(**validated_data)


class FavoriteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de favorites"""
    
    service_id = serializers.IntegerField(source='service.id', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    service_price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    service_rating = serializers.DecimalField(source='service.rating_avg', max_digits=3, decimal_places=2, read_only=True)
    provider_name = serializers.CharField(source='service.provider.full_name', read_only=True)
    category_name = serializers.CharField(source='service.category.name', read_only=True)
    
    class Meta:
        model = Favorite
        fields = [
            'id', 'service_id', 'service_title', 'service_price', 
            'service_rating', 'provider_name', 'category_name', 'created_at'
        ]


class FavoriteCheckSerializer(serializers.Serializer):
    """Serializer para verificar si un servicio está en favoritos"""
    
    service_id = serializers.IntegerField()
    is_favorite = serializers.BooleanField(read_only=True)
    
    def validate_service_id(self, value):
        """Validar que el servicio existe"""
        try:
            Service.objects.get(id=value, is_active=True, is_published=True)
        except Service.DoesNotExist:
            raise serializers.ValidationError("El servicio no existe o no está disponible")
        return value
