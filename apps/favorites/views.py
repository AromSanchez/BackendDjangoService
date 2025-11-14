"""
Views para el módulo de favorites
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from conectaya.authentication.decorators import jwt_required_drf
from apps.users.models import User
from apps.services.models import Service
from .models import Favorite
from .serializers import (
    FavoriteSerializer, FavoriteListSerializer, 
    FavoriteCreateSerializer, FavoriteCheckSerializer
)


@api_view(['GET', 'POST'])
@jwt_required_drf
def favorites_list_create(request):
    """
    GET: Lista favoritos del usuario autenticado
    POST: Agrega un servicio a favoritos
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if request.method == 'GET':
            # Lista favoritos del usuario
            favorites = Favorite.objects.filter(user_id=user_id).order_by('-created_at')
            
            # Filtros opcionales
            category = request.GET.get('category')
            if category:
                favorites = favorites.filter(service__category__slug=category)
            
            serializer = FavoriteListSerializer(favorites, many=True)
            return Response({
                'favorites': serializer.data,
                'count': favorites.count()
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Agregar a favoritos
            data = request.data.copy()
            serializer = FavoriteCreateSerializer(data=data)
            
            if serializer.is_valid():
                service = serializer.validated_data['service']
                
                # Verificar que no esté ya en favoritos
                existing_favorite = Favorite.objects.filter(
                    user_id=user_id, 
                    service=service
                ).first()
                
                if existing_favorite:
                    return Response(
                        {'error': 'El servicio ya está en favoritos'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # No se puede agregar el propio servicio a favoritos
                if service.provider_id == user_id:
                    return Response(
                        {'error': 'No puedes agregar tu propio servicio a favoritos'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                favorite = serializer.save(user_id=user_id)
                
                return Response(
                    FavoriteSerializer(favorite).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@jwt_required_drf
def favorite_remove(request, service_id):
    """
    Quitar un servicio de favoritos
    """
    try:
        user_id = request.jwt_user_id
        service = get_object_or_404(Service, id=service_id)
        
        favorite = get_object_or_404(
            Favorite, 
            user_id=user_id, 
            service=service
        )
        
        favorite.delete()
        
        return Response(
            {'message': 'Servicio removido de favoritos'},
            status=status.HTTP_204_NO_CONTENT
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def favorite_check(request, service_id):
    """
    Verificar si un servicio está en favoritos
    """
    try:
        user_id = request.jwt_user_id
        service = get_object_or_404(Service, id=service_id)
        
        is_favorite = Favorite.objects.filter(
            user_id=user_id, 
            service=service
        ).exists()
        
        return Response({
            'service_id': service_id,
            'is_favorite': is_favorite
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def favorites_stats(request):
    """
    Estadísticas de favoritos del usuario
    """
    try:
        user_id = request.jwt_user_id
        
        favorites = Favorite.objects.filter(user_id=user_id)
        total_favorites = favorites.count()
        
        # Estadísticas por categoría
        categories_stats = []
        from django.db.models import Count
        
        category_counts = favorites.values(
            'service__category__name',
            'service__category__slug'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        for item in category_counts:
            categories_stats.append({
                'category_name': item['service__category__name'],
                'category_slug': item['service__category__slug'],
                'count': item['count']
            })
        
        # Servicios favoritos más recientes
        recent_favorites = favorites.order_by('-created_at')[:5]
        recent_serializer = FavoriteListSerializer(recent_favorites, many=True)
        
        return Response({
            'total_favorites': total_favorites,
            'categories_stats': categories_stats,
            'recent_favorites': recent_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def favorite_toggle(request, service_id):
    """
    Alternar estado de favorito (agregar/quitar)
    """
    try:
        user_id = request.jwt_user_id
        service = get_object_or_404(Service, id=service_id)
        
        # Verificar que el servicio esté disponible
        if not service.is_active or not service.is_published:
            return Response(
                {'error': 'El servicio no está disponible'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # No se puede agregar el propio servicio a favoritos
        if service.provider_id == user_id:
            return Response(
                {'error': 'No puedes agregar tu propio servicio a favoritos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        favorite = Favorite.objects.filter(
            user_id=user_id, 
            service=service
        ).first()
        
        if favorite:
            # Quitar de favoritos
            favorite.delete()
            return Response({
                'service_id': service_id,
                'is_favorite': False,
                'message': 'Servicio removido de favoritos'
            }, status=status.HTTP_200_OK)
        else:
            # Agregar a favoritos
            favorite = Favorite.objects.create(
                user_id=user_id,
                service=service
            )
            return Response({
                'service_id': service_id,
                'is_favorite': True,
                'message': 'Servicio agregado a favoritos'
            }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
