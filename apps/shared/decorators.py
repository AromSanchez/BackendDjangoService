"""
Decoradores personalizados para validación de permisos
"""
import jwt
from functools import wraps
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status


def jwt_required_drf(view_func):
    """
    Decorador para validar JWT de Spring Boot en Django
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return Response(
                {'error': 'Token no proporcionado'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decodificar JWT con la misma clave que Spring Boot
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256']
            )
            
            # Agregar datos del usuario al request
            request.jwt_user_id = payload.get('userId')
            request.jwt_user_email = payload.get('email')
            request.jwt_user_role = payload.get('role')
            
        except jwt.ExpiredSignatureError:
            return Response(
                {'error': 'Token expirado'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except jwt.InvalidTokenError:
            return Response(
                {'error': 'Token inválido'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def role_required(allowed_roles):
    """
    Decorador para validar roles
    Uso: @role_required(['PROVIDER', 'ADMIN'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_role = getattr(request, 'jwt_user_role', None)
            
            if not user_role:
                return Response(
                    {'error': 'No se pudo determinar el rol del usuario'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if user_role not in allowed_roles:
                return Response(
                    {'error': f'Se requiere uno de estos roles: {", ".join(allowed_roles)}'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
