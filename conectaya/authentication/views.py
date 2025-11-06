"""
Vistas de ejemplo para demostrar el uso de autenticación JWT
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .decorators import jwt_required, jwt_required_drf


# ============================================
# VISTA DJANGO ESTÁNDAR
# ============================================

@jwt_required
def protected_view(request):
    """
    Vista protegida con JWT - Django estándar
    
    Ejemplo de uso:
        GET /api/protected/
        Header: Authorization: Bearer <tu_token_jwt>
    """
    user_id = request.jwt_user_id
    
    return JsonResponse({
        'message': f'Usuario autenticado con ID: {user_id}',
        'user_id': user_id,
        'authenticated': True
    })


# ============================================
# VISTA DJANGO REST FRAMEWORK
# ============================================

@api_view(['GET'])
@jwt_required_drf
def protected_view_drf(request):
    """
    Vista protegida con JWT - Django REST Framework
    
    Ejemplo de uso:
        GET /api/protected-drf/
        Header: Authorization: Bearer <tu_token_jwt>
    """
    user_id = request.jwt_user_id
    
    return Response({
        'message': f'Usuario autenticado con ID: {user_id}',
        'user_id': user_id,
        'authenticated': True,
        'framework': 'Django REST Framework'
    })


@api_view(['GET'])
@jwt_required_drf
def user_info(request):
    """
    Obtiene información del usuario autenticado
    
    Ejemplo de uso:
        GET /api/user-info/
        Header: Authorization: Bearer <tu_token_jwt>
    """
    user_id = request.jwt_user_id
    
    # Aquí podrías hacer queries a tu base de datos
    # para obtener más información del usuario
    from django.contrib.auth.models import User
    user = User.objects.filter(id=user_id).first()
    
    return Response({
        'user_id': user_id,
        'email': user.email if user else None,
        'username': user.username if user else None,
        'message': 'Usuario autenticado correctamente',
        'token_valid': True
    })


# ============================================
# VISTA PÚBLICA (SIN PROTECCIÓN)
# ============================================

@api_view(['GET'])
def public_view(request):
    """
    Vista pública que no requiere autenticación
    """
    return Response({
        'message': 'Esta es una vista pública',
        'requires_auth': False
    })
