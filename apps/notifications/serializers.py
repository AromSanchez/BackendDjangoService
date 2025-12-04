from rest_framework import serializers
from .models import DeviceToken


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['token', 'device_type']
    
    def create(self, validated_data):
        user = self.context['request'].user
        token = validated_data['token']
        
        # Actualizar o crear token
        device_token, created = DeviceToken.objects.update_or_create(
            user=user,
            token=token,
            defaults={'device_type': validated_data.get('device_type', 'ANDROID')}
        )
        
        return device_token
