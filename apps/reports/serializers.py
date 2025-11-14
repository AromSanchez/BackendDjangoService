"""
Serializers para el módulo de reports
"""
from rest_framework import serializers
from .models import Report
from apps.users.models import User
from apps.services.models import Service
from apps.bookings.models import Booking


class ReporterSerializer(serializers.ModelSerializer):
    """Serializer básico para reporter"""
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email']


class ReportedUserSerializer(serializers.ModelSerializer):
    """Serializer básico para usuario reportado"""
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'role']


class ServiceBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para servicio en reports"""
    
    class Meta:
        model = Service
        fields = ['id', 'title', 'provider_id']


class BookingBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para booking en reports"""
    
    class Meta:
        model = Booking
        fields = ['id', 'status', 'created_at']


class ReportSerializer(serializers.ModelSerializer):
    """Serializer completo para reports"""
    
    reporter = ReporterSerializer(read_only=True)
    reported_user = ReportedUserSerializer(read_only=True)
    service = ServiceBasicSerializer(read_only=True)
    booking = BookingBasicSerializer(read_only=True)
    admin_user = ReporterSerializer(read_only=True)
    
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'reporter_id', 'reporter', 'reported_user_id', 'reported_user',
            'booking', 'service', 'reason', 'reason_display', 'description',
            'status', 'status_display', 'admin_user_id', 'admin_user',
            'admin_notes', 'resolved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reporter_id', 'admin_user_id', 'resolved_at', 
            'created_at', 'updated_at'
        ]


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear reports"""
    
    class Meta:
        model = Report
        fields = [
            'reported_user_id', 'booking', 'service', 
            'reason', 'description'
        ]
    
    def validate(self, data):
        """Validaciones personalizadas"""
        reported_user_id = data.get('reported_user_id')
        booking = data.get('booking')
        service = data.get('service')
        
        # Debe reportar al menos un usuario o un servicio
        if not reported_user_id and not service:
            raise serializers.ValidationError(
                "Debe especificar un usuario o servicio a reportar"
            )
        
        # Si hay booking, verificar que el usuario esté involucrado
        if booking:
            request = self.context.get('request')
            user_id = request.jwt_user_id if request else None
            
            if user_id not in [booking.customer_id, booking.provider_id]:
                raise serializers.ValidationError(
                    "Solo puedes reportar bookings en los que participas"
                )
        
        return data
    
    def create(self, validated_data):
        """Crear un nuevo report"""
        return Report.objects.create(**validated_data)


class ReportListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de reports"""
    
    reported_user_name = serializers.CharField(source='reported_user.full_name', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'reported_user_name', 'service_title', 'reason', 
            'reason_display', 'status', 'status_display', 'created_at'
        ]


class ReportModerationSerializer(serializers.ModelSerializer):
    """Serializer para moderación de reports (admin)"""
    
    reporter = ReporterSerializer(read_only=True)
    reported_user = ReportedUserSerializer(read_only=True)
    service = ServiceBasicSerializer(read_only=True)
    booking = BookingBasicSerializer(read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reported_user', 'booking', 'service',
            'reason', 'description', 'status', 'admin_notes',
            'resolved_at', 'created_at', 'updated_at'
        ]
    
    def update(self, instance, validated_data):
        """Actualizar estado de moderación"""
        from django.utils import timezone
        
        allowed_fields = ['status', 'admin_notes']
        
        for attr, value in validated_data.items():
            if attr in allowed_fields:
                setattr(instance, attr, value)
        
        # Si se marca como resuelto, agregar timestamp
        if validated_data.get('status') in ['resolved', 'dismissed']:
            instance.resolved_at = timezone.now()
            # Agregar admin_user_id desde el request
            request = self.context.get('request')
            if request and hasattr(request, 'jwt_user_id'):
                instance.admin_user_id = request.jwt_user_id
        
        instance.save()
        return instance
