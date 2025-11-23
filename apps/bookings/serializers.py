"""
Serializers para el módulo de bookings
"""
from rest_framework import serializers
from .models import Booking
from apps.services.serializers import ServiceSerializer
from apps.users.models import User


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer básico para cliente"""
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone_number']


class ProviderSerializer(serializers.ModelSerializer):
    """Serializer básico para proveedor"""
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone_number']


class BookingSerializer(serializers.ModelSerializer):
    """Serializer completo para bookings"""
    
    service = ServiceSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)
    provider = ProviderSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'service', 'customer_id', 'provider_id', 'customer', 'provider',
            'status', 'status_display', 'service_price', 'booking_date', 'booking_time', 
            'booking_notes', 'customer_address', 'accepted_at', 'in_progress_at',
            'completed_at', 'canceled_at', 'cancellation_reason', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'customer_id', 'provider_id', 'accepted_at', 'in_progress_at',
            'completed_at', 'canceled_at', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """Crear un nuevo booking"""
        # Capturar el precio del servicio al momento de crear el booking
        service = validated_data.get('service')
        if service and not validated_data.get('service_price'):
            validated_data['service_price'] = service.price
        return Booking.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Actualizar un booking existente"""
        # Solo permitir actualizar ciertos campos según el estado
        allowed_fields = ['booking_date', 'booking_time', 'booking_notes', 
                         'customer_address', 'status', 'cancellation_reason']
        
        for attr, value in validated_data.items():
            if attr in allowed_fields:
                setattr(instance, attr, value)
        
        instance.save()
        return instance


class BookingListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de bookings"""
    
    service_title = serializers.CharField(source='service.title', read_only=True)
    service_price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    provider_name = serializers.CharField(source='provider.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'service_id', 'service_title', 'service_price', 
            'customer_id', 'customer_name', 
            'provider_id', 'provider_name',
            'status', 'status_display', 'booking_date', 'booking_time', 'created_at',
            'booking_notes'
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear bookings"""
    
    class Meta:
        model = Booking
        fields = [
            'service', 'booking_date', 'booking_time', 
            'booking_notes', 'customer_address'
        ]
    
    def validate(self, data):
        """Validaciones personalizadas"""
        service = data.get('service')
        
        # Verificar que el servicio esté activo y publicado
        if not service.is_active or not service.is_published:
            raise serializers.ValidationError("El servicio no está disponible")
        
        return data


class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar solo el estado"""
    
    class Meta:
        model = Booking
        fields = ['status', 'cancellation_reason']
    
    def validate_status(self, value):
        """Validar transiciones de estado"""
        instance = self.instance
        current_status = instance.status if instance else None
        
        # Definir transiciones válidas
        valid_transitions = {
            'pending': ['accepted', 'rejected', 'canceled_by_customer'],
            'negotiating': ['accepted', 'rejected', 'canceled_by_customer', 'canceled_by_provider'],
            'accepted': ['in_progress', 'completed', 'canceled_by_customer', 'canceled_by_provider'],
            'in_progress': ['completed', 'canceled_by_provider'],
            'completed': [],  # Estado final
            'canceled_by_customer': [],  # Estado final
            'canceled_by_provider': [],  # Estado final
            'rejected': []  # Estado final
        }
        
        if current_status and value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"No se puede cambiar de '{current_status}' a '{value}'"
            )
        
        return value
