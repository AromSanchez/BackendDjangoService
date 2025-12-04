from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import DeviceToken
from .serializers import DeviceTokenSerializer


class NotificationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='register-token')
    def register_token(self, request):
        """
        Registrar token FCM del dispositivo
        POST /api/notifications/register-token/
        Body: {"token": "fcm_token_here", "device_type": "ANDROID"}
        """
        serializer = DeviceTokenSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Token registrado exitosamente'}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'], url_path='unregister-token')
    def unregister_token(self, request):
        """
        Eliminar token FCM del dispositivo
        DELETE /api/notifications/unregister-token/
        Body: {"token": "fcm_token_here"}
        """
        token = request.data.get('token')
        
        if not token:
            return Response({'error': 'Token requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count, _ = DeviceToken.objects.filter(user=request.user, token=token).delete()
        
        if deleted_count > 0:
            return Response({'message': 'Token eliminado exitosamente'}, status=status.HTTP_200_OK)
        
        return Response({'error': 'Token no encontrado'}, status=status.HTTP_404_NOT_FOUND)
