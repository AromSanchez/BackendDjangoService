"""
Serializers para el módulo de users
"""
from rest_framework import serializers
from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer completo para usuarios"""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    provider_status_display = serializers.CharField(source='get_provider_status_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'phone_verified_at',
            'role', 'role_display', 'is_active', 'provider_status', 
            'provider_status_display', 'created_at'
        ]
        read_only_fields = [
            'id', 'email', 'role', 'provider_status', 'created_at'
        ]


class UserBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para usuarios"""
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'role']


class UserPublicSerializer(serializers.ModelSerializer):
    """Serializer público para usuarios (sin datos sensibles)"""
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'role', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer completo para perfiles de usuario"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user_id', 'user', 'bio', 'avatar_file_id', 
            'city', 'country', 'notification_email', 'notification_push',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Include phone_number in the user object"""
        representation = super().to_representation(instance)
        if representation.get('user') and instance.user:
            representation['user']['phone_number'] = instance.user.phone_number
        return representation
    
    def create(self, validated_data):
        """Crear un nuevo perfil de usuario"""
        return UserProfile.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Actualizar perfil de usuario"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear perfiles de usuario"""
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'avatar_file_id', 'city', 'country', 
            'notification_email', 'notification_push'
        ]
    
    def validate_bio(self, value):
        """Validar longitud de biografía"""
        if value and len(value) > 500:
            raise serializers.ValidationError("La biografía no puede exceder 500 caracteres")
        return value


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar perfiles de usuario"""
    
    phone_number = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserProfile
        fields = [
            'bio', 'avatar_file_id', 'city', 'country', 
            'notification_email', 'notification_push',
            'phone_number'
        ]
    
    def validate_bio(self, value):
        """Validar longitud de biografía"""
        if value and len(value) > 500:
            raise serializers.ValidationError("La biografía no puede exceder 500 caracteres")
        return value

    def update(self, instance, validated_data):
        phone_number = validated_data.pop('phone_number', None)
        
        # Update UserProfile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        # Sanitize UserProfile boolean fields if they are bytes
        for field in ['notification_email', 'notification_push']:
            val = getattr(instance, field)
            if isinstance(val, bytes):
                setattr(instance, field, val == b'\x01')
                
        instance.save()

        # Update User phone_number if provided
        if phone_number:
            user = instance.user
            user.phone_number = phone_number
            
            # Sanitize User boolean fields if they are bytes (fix for managed=False models)
            if isinstance(user.is_active, bytes):
                user.is_active = user.is_active == b'\x01'
                
            user.save()
            
        return instance


class UserProfilePublicSerializer(serializers.ModelSerializer):
    """Serializer público para perfiles (sin configuraciones privadas)"""
    
    user = UserPublicSerializer(read_only=True)
    completed_services_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'bio', 'avatar_file_id', 'city', 'country', 'created_at',
            'completed_services_count', 'average_rating', 'total_reviews'
        ]
    
    def to_representation(self, instance):
        """Include phone_number in the user object"""
        representation = super().to_representation(instance)
        if representation.get('user') and instance.user:
            representation['user']['phone_number'] = instance.user.phone_number
        return representation

    def get_completed_services_count(self, obj):
        from apps.bookings.models import Booking
        return Booking.objects.filter(
            provider_id=obj.user_id,
            status='completed'
        ).count()

    def get_average_rating(self, obj):
        from apps.services.models import Service
        # Solo considerar servicios que tienen reseñas
        services = Service.objects.filter(
            provider_id=obj.user_id, 
            reviews_count__gt=0
        )
        
        if not services.exists():
            return 0.0
        
        total_rating = sum(s.rating_avg for s in services)
        return round(total_rating / services.count(), 1)

    def get_total_reviews(self, obj):
        from apps.reviews.models import Review
        return Review.objects.filter(
            service__provider_id=obj.user_id,
            is_visible=True
        ).count()


class UserListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de usuarios"""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    provider_status_display = serializers.CharField(source='get_provider_status_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'role', 'role_display',
            'provider_status', 'provider_status_display', 'is_active', 'created_at'
        ]


class UserAdminSerializer(serializers.ModelSerializer):
    """Serializer para administración de usuarios"""
    
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'phone_verified_at',
            'role', 'is_active', 'provider_status', 'profile', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'created_at']
    
    def update(self, instance, validated_data):
        """Actualizar usuario (solo admin)"""
        # Solo permitir actualizar ciertos campos
        allowed_fields = ['full_name', 'phone_number', 'is_active', 'provider_status']
        
        for attr, value in validated_data.items():
            if attr in allowed_fields:
                setattr(instance, attr, value)
        
        instance.save()
        return instance
