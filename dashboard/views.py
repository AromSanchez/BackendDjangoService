"""
Views para el módulo Dashboard
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from conectaya.authentication.decorators import jwt_required_drf
from .models import User
from .services import DashboardService
from .serializers import DashboardDataSerializer


@api_view(['GET'])
@jwt_required_drf
def dashboard_view(request):
    """
    Endpoint protegido del Dashboard
    
    Retorna datos personalizados según el rol del usuario autenticado.
    
    Roles soportados:
    - CUSTOMER: Productos, ofertas, pedidos
    - PROVIDER: Servicios, pedidos, ingresos
    - ADMIN: Usuarios, reportes, estadísticas
    
    Headers requeridos:
        Authorization: Bearer <jwt_token>
    
    Respuesta:
        {
            "role": "CUSTOMER|PROVIDER|ADMIN",
            "user": {
                "id": 1,
                "full_name": "...",
                "email": "...",
                ...
            },
            "data": {
                // Datos específicos según el rol
            },
            "message": "..."
        }
    """
    try:
        # Obtener el ID del usuario del token JWT
        user_id = request.jwt_user_id
        
        # Buscar el usuario en la base de datos
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {
                    'error': 'Usuario no encontrado',
                    'detail': f'No existe un usuario con ID {user_id}'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar que el usuario esté activo
        if not user.is_active:
            return Response(
                {
                    'error': 'Usuario inactivo',
                    'detail': 'Tu cuenta ha sido desactivada. Contacta al administrador.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener datos del dashboard según el rol
        dashboard_data = DashboardService.get_dashboard_data(user)
        
        # Serializar la respuesta
        serializer = DashboardDataSerializer(dashboard_data)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': 'Error interno del servidor',
                'detail': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def user_profile_view(request):
    """
    Endpoint para obtener el perfil del usuario autenticado
    
    Headers requeridos:
        Authorization: Bearer <jwt_token>
    
    Respuesta:
        {
            "id": 1,
            "full_name": "...",
            "email": "...",
            "role": "...",
            ...
        }
    """
    try:
        user_id = request.jwt_user_id
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from .serializers import UserSerializer
        serializer = UserSerializer(user)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
