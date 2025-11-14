"""
Serializers para el módulo de servicios
"""
from rest_framework import serializers
from .models import Service, Category, ServiceImage
from apps.users.models import User


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para categorías"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_active']


class ServiceImageSerializer(serializers.ModelSerializer):
    """Serializer para imágenes de servicios"""
    
    class Meta:
        model = ServiceImage
        fields = ['id', 'file_id', 'order']


class ProviderSerializer(serializers.ModelSerializer):
    """Serializer básico para proveedor"""
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone']


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer para servicios"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    provider = ProviderSerializer(read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)
    average_rating = serializers.DecimalField(source='rating_avg', max_digits=3, decimal_places=2, read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'provider_id', 'category', 'category_name', 'provider',
            'title', 'description', 'price', 'location_type',
            'is_published', 'is_active', 'created_at', 'updated_at',
            'reviews_count', 'average_rating', 'favorites_count',
            'views_count', 'bookings_count', 'images'
        ]
        read_only_fields = ['id', 'provider_id', 'created_at', 'updated_at', 
                           'reviews_count', 'rating_sum', 'rating_avg', 
                           'favorites_count', 'views_count', 'bookings_count']
    
    def create(self, validated_data):
        """Crear un nuevo servicio"""
        return Service.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Actualizar un servicio existente"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ServiceListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de servicios"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    provider_name = serializers.CharField(source='provider.full_name', read_only=True)
    average_rating = serializers.DecimalField(source='rating_avg', max_digits=3, decimal_places=2, read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'description', 'price', 'location_type',
            'category_name', 'provider_name', 'average_rating',
            'reviews_count', 'favorites_count', 'created_at', 'is_published'
        ]
