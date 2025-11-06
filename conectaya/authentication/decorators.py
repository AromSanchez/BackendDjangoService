"""
Decoradores para proteger vistas con autenticación JWT
"""
from functools import wraps
from django.http import JsonResponse
from .jwt_utils import JWTUtils


def jwt_required(view_func):
    """
    Decorador que requiere un JWT token válido para acceder a la vista
    
    Uso:
        @jwt_required
        def mi_vista(request):
            user_id = request.jwt_user_id
            return JsonResponse({'message': f'Usuario ID: {user_id}'})
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Obtener el header Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'error': 'Token no proporcionado'},
                status=401
            )
        
        # Extraer el token
        token = auth_header[7:]
        
        # Validar el token
        user_id = JWTUtils.get_user_id_from_token(token)
        
        if not user_id:
            return JsonResponse(
                {'error': 'Token inválido o expirado'},
                status=401
            )
        
        # Adjuntar información al request
        request.jwt_user_id = user_id
        request.jwt_token = token
        
        # Llamar a la vista original
        return view_func(request, *args, **kwargs)
    
    return wrapper


def jwt_required_drf(view_func):
    """
    Decorador para vistas de Django REST Framework
    
    Uso:
        @api_view(['GET'])
        @jwt_required_drf
        def mi_vista(request):
            user_id = request.jwt_user_id
            return Response({'message': f'Usuario ID: {user_id}'})
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Obtener el header Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            from rest_framework.response import Response
            return Response(
                {'error': 'Token no proporcionado'},
                status=401
            )
        
        # Extraer el token
        token = auth_header[7:]
        
        # Validar el token
        user_id = JWTUtils.get_user_id_from_token(token)
        
        if not user_id:
            from rest_framework.response import Response
            return Response(
                {'error': 'Token inválido o expirado'},
                status=401
            )
        
        # Adjuntar información al request
        request.jwt_user_id = user_id
        request.jwt_token = token
        
        # Llamar a la vista original
        return view_func(request, *args, **kwargs)
    
    return wrapper
