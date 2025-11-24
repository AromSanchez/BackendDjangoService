"""
Serializers para el módulo de servicios
"""
from rest_framework import serializers
from django.db import models
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
        fields = ['id', 'full_name', 'email', 'phone_number']


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer para servicios"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    provider = ProviderSerializer(read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)
    average_rating = serializers.DecimalField(source='rating_avg', max_digits=3, decimal_places=2, read_only=True)
    status = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    requests_count = serializers.SerializerMethodField()
    completed_count = serializers.SerializerMethodField()
    
    # Campos adicionales del frontend (opcionales)
    location = serializers.CharField(write_only=True, required=False, allow_blank=True)
    duration_hours = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    requirements = serializers.CharField(write_only=True, required=False, allow_blank=True)
    terms_conditions = serializers.CharField(write_only=True, required=False, allow_blank=True)
    image_file_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Service
        fields = [
            'id', 'provider_id', 'category', 'category_name', 'provider',
            'title', 'description', 'price', 'location_type',
            'is_published', 'is_active', 'status', 'created_at', 'updated_at',
            'reviews_count', 'average_rating', 'favorites_count',
            'views_count', 'bookings_count', 'images', 'is_favorite',
            'requests_count', 'completed_count',
            # Campos adicionales del frontend
            'location', 'duration_hours', 'requirements', 'terms_conditions', 'image_file_ids'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 
                           'reviews_count', 'rating_sum', 'rating_avg', 
                           'favorites_count', 'views_count', 'bookings_count']
    
    def validate_category(self, value):
        """Validar y convertir categoría"""
        if isinstance(value, str):
            # Si es string, buscar por slug o nombre
            try:
                category = Category.objects.get(
                    models.Q(slug__icontains=value.lower()) | 
                    models.Q(name__icontains=value)
                )
                return category
            except Category.DoesNotExist:
                # Si no encuentra, usar la primera categoría disponible
                first_category = Category.objects.first()
                if first_category:
                    return first_category
                raise serializers.ValidationError(f"No se encontró la categoría: {value}")
        return value
    
    def validate_price(self, value):
        """Validar precio"""
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0")
        return value

    def get_status(self, obj):
        """Estado amigable para el frontend"""
        if not obj.is_published:
            return "PENDING"
        if not obj.is_active:
            return "INACTIVE"
        return "ACTIVE"
    
    
    def get_is_favorite(self, obj):
        """Check if service is favorited by current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'jwt_user_id'):
            from apps.favorites.models import Favorite
            return Favorite.objects.filter(
                user_id=request.jwt_user_id,
                service=obj
            ).exists()
        return False
    
    def get_requests_count(self, obj):
        """Get total number of bookings/requests for this service"""
        from apps.bookings.models import Booking
        return Booking.objects.filter(service_id=obj.id).count()
    
    def get_completed_count(self, obj):
        """Get number of completed bookings for this service"""
        from apps.bookings.models import Booking
        return Booking.objects.filter(service_id=obj.id, status='completed').count()
    
    def create(self, validated_data):
        """Crear un nuevo servicio"""
        # Valores por defecto para asegurar que el servicio quede activo/publicado
        validated_data.setdefault('is_active', True)
        validated_data.setdefault('is_published', True)
        validated_data.setdefault('location_type', validated_data.get('location_type'))
        # Mapear location a location_type
        if 'location' in validated_data:
            validated_data['location_type'] = validated_data.pop('location')
        
        # Extraer image_file_ids antes de crear el servicio
        image_file_ids = validated_data.pop('image_file_ids', [])
        
        # Remover campos que no están en el modelo
        extra_fields = ['duration_hours', 'requirements', 'terms_conditions']
        for field in extra_fields:
            validated_data.pop(field, None)
        
        # Crear el servicio
        service = Service.objects.create(**validated_data)
        
        # Crear las imágenes del servicio si hay file_ids
        if image_file_ids:
            for index, file_id in enumerate(image_file_ids):
                ServiceImage.objects.create(
                    service=service,
                    file_id=file_id,
                    order=index
                )
        
        return service
    
    def update(self, instance, validated_data):
        """Actualizar un servicio existente"""
        # Mapear location a location_type
        if 'location' in validated_data:
            validated_data['location_type'] = validated_data.pop('location')
        
        # Extraer image_file_ids antes de actualizar el servicio
        image_file_ids = validated_data.pop('image_file_ids', None)
        
        # Remover campos que no están en el modelo
        extra_fields = ['duration_hours', 'requirements', 'terms_conditions']
        for field in extra_fields:
            validated_data.pop(field, None)
        
        # Actualizar el servicio
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar las imágenes del servicio si se proporcionaron nuevos file_ids
        if image_file_ids is not None:
            # Eliminar imágenes existentes
            instance.images.all().delete()
            
            # Crear nuevas imágenes
            for index, file_id in enumerate(image_file_ids):
                ServiceImage.objects.create(
                    service=instance,
                    file_id=file_id,
                    order=index
                )
        
        return instance


class ServiceListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de servicios"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    provider_name = serializers.CharField(source='provider.full_name', read_only=True)
    average_rating = serializers.DecimalField(source='rating_avg', max_digits=3, decimal_places=2, read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)
    is_favorite = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'description', 'price', 'location_type',
            'category_name', 'provider_name', 'average_rating',
            'reviews_count', 'favorites_count', 'created_at', 'is_published',
            'images', 'is_favorite'
        ]
    
    def get_is_favorite(self, obj):
        """Check if service is favorited by current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'jwt_user_id'):
            from apps.favorites.models import Favorite
            return Favorite.objects.filter(
                user_id=request.jwt_user_id,
                service=obj
            ).exists()
        return False

