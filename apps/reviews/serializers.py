"""
Serializers para el módulo de reviews
"""
from rest_framework import serializers
from .models import Review
from apps.services.models import Service
from apps.bookings.models import Booking
from apps.users.models import User


class ReviewerSerializer(serializers.ModelSerializer):
    """Serializer básico para reviewer"""
    
    class Meta:
        model = User
        fields = ['id', 'full_name']


class ServiceBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para servicio en reviews"""
    
    class Meta:
        model = Service
        fields = ['id', 'title', 'price']


class BookingBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para booking en reviews"""
    
    class Meta:
        model = Booking
        fields = ['id', 'booking_date', 'status']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer completo para reviews"""
    
    reviewer = ReviewerSerializer(read_only=True)
    service = ServiceBasicSerializer(read_only=True)
    booking = BookingBasicSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer_id', 'reviewer', 'service', 'booking',
            'rating', 'comment', 'is_visible', 'is_flagged', 
            'flagged_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reviewer_id', 'is_visible', 'is_flagged', 
            'flagged_reason', 'created_at', 'updated_at'
        ]
    
    def validate_rating(self, value):
        """Validar que el rating esté entre 1 y 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("El rating debe estar entre 1 y 5")
        return value
    
    def validate(self, data):
        """Validaciones personalizadas"""
        booking = data.get('booking')
        service = data.get('service')
        
        # Si hay booking, verificar que esté completado
        if booking and booking.status != 'completed':
            raise serializers.ValidationError(
                "Solo se pueden reseñar servicios completados"
            )
        
        # Si hay booking, verificar que el servicio coincida
        if booking and service and booking.service != service:
            raise serializers.ValidationError(
                "El servicio no coincide con el booking"
            )
        
        return data


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear reviews"""
    
    class Meta:
        model = Review
        fields = ['service', 'booking', 'rating', 'comment']
    
    def validate_service(self, value):
        """Validar que el servicio existe y está activo"""
        if not value.is_active:
            raise serializers.ValidationError("El servicio no está activo")
        return value
    
    def validate_booking(self, value):
        """Validar el booking si se proporciona"""
        if value and value.status != 'completed':
            raise serializers.ValidationError(
                "Solo se pueden reseñar bookings completados"
            )
        return value
    
    def create(self, validated_data):
        """Crear una nueva review"""
        return Review.objects.create(**validated_data)


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar reviews"""
    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
    
    def validate_rating(self, value):
        """Validar que el rating esté entre 1 y 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("El rating debe estar entre 1 y 5")
        return value


class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de reviews"""
    
    reviewer_name = serializers.CharField(source='reviewer.full_name', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer_name', 'service_title', 'rating', 
            'comment', 'created_at', 'is_visible'
        ]


class ReviewModerationSerializer(serializers.ModelSerializer):
    """Serializer para moderación de reviews (admin)"""
    
    reviewer = ReviewerSerializer(read_only=True)
    service = ServiceBasicSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'service', 'rating', 'comment',
            'is_visible', 'is_flagged', 'flagged_reason', 
            'created_at', 'updated_at'
        ]
    
    def update(self, instance, validated_data):
        """Actualizar estado de moderación"""
        allowed_fields = ['is_visible', 'is_flagged', 'flagged_reason']
        
        for attr, value in validated_data.items():
            if attr in allowed_fields:
                setattr(instance, attr, value)
        
        instance.save()
        return instance
