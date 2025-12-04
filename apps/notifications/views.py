from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import DeviceToken
from .serializers import DeviceTokenSerializer
import jwt
import logging

logger = logging.getLogger(__name__)


class NotificationViewSet(viewsets.ViewSet):
    
    def get_permissions(self):
        """
        Permitir registro de token sin autenticación,
        pero requerir autenticación para desregistro
        """
        if self.action == 'register_token':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['post'], url_path='register-token')
    def register_token(self, request):
        """
        Registrar token FCM del dispositivo
        POST /api/notifications/register-token/
        Body: {"token": "fcm_token_here", "device_type": "ANDROID"}
        Header: Authorization: Bearer <jwt_token> (requerido)
        """
        # Extraer el JWT del header Authorization
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return Response(
                {'error': 'Token de autenticación requerido'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token_jwt = auth_header.split(' ')[1]
        
        try:
            # Decodificar el JWT de Spring Boot (sin verificar la firma por ahora)
            decoded = jwt.decode(token_jwt, options={"verify_signature": False})
            user_id = decoded.get('userId')
            
            if not user_id:
                return Response(
                    {'error': 'Token inválido: userId no encontrado'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            logger.info(f"📱 Registrando token FCM para user_id={user_id}")
            
            # Obtener el token FCM del body
            fcm_token = request.data.get('token')
            device_type = request.data.get('device_type', 'ANDROID')
            
            if not fcm_token:
                return Response(
                    {'error': 'Token FCM requerido'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear o actualizar el token del dispositivo
            # Crear o actualizar el token del dispositivo
            # Si el token ya existe (incluso para otro usuario), lo actualizamos para este usuario
            device_token, created = DeviceToken.objects.update_or_create(
                token=fcm_token,
                defaults={
                    'user_id': user_id,
                    'device_type': device_type
                }
            )
            
            action_msg = "creado" if created else "actualizado"
            logger.info(f"✅ Token FCM {action_msg} para user_id={user_id}")
            
            return Response(
                {'message': f'Token {action_msg} exitosamente'}, 
                status=status.HTTP_201_CREATED
            )
            
        except jwt.DecodeError:
            return Response(
                {'error': 'Token JWT inválido'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"❌ Error al registrar token: {str(e)}")
            return Response(
                {'error': 'Error al registrar token'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
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
