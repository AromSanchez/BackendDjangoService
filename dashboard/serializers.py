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
