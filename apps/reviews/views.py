"""
Views para el módulo de reviews
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from conectaya.authentication.decorators import jwt_required_drf
from apps.users.models import User
from apps.services.models import Service
from apps.bookings.models import Booking
from .models import Review
from .serializers import (
    ReviewSerializer, ReviewListSerializer, ReviewCreateSerializer,
    ReviewUpdateSerializer, ReviewModerationSerializer
)


@api_view(['GET', 'POST'])
@jwt_required_drf
def reviews_list_create(request):
    """
    GET: Lista reviews del usuario autenticado
    POST: Crea una nueva review
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if request.method == 'GET':
            # Lista reviews del usuario
            reviews = Review.objects.filter(reviewer_id=user_id, is_visible=True)
            reviews = reviews.order_by('-created_at')
            
            serializer = ReviewListSerializer(reviews, many=True)
            return Response({
                'reviews': serializer.data,
                'count': reviews.count()
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Solo clientes pueden crear reviews
            if user.role != 'CUSTOMER':
                return Response(
                    {'error': 'Solo los clientes pueden crear reseñas'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Crear review
            data = request.data.copy()
            serializer = ReviewCreateSerializer(data=data)
            
            if serializer.is_valid():
                # Verificar que no exista ya una review para este booking
                booking = serializer.validated_data.get('booking')
                service = serializer.validated_data['service']
                
                if booking:
                    existing_review = Review.objects.filter(booking=booking).first()
                    if existing_review:
                        return Response(
                            {'error': 'Ya existe una reseña para este booking'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Verificar que el usuario sea el cliente del booking
                    if booking.customer_id != user_id:
                        return Response(
                            {'error': 'Solo puedes reseñar tus propios bookings'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                
                review = serializer.save(reviewer_id=user_id)
                
                return Response(
                    ReviewSerializer(review).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT', 'DELETE'])
@jwt_required_drf
def review_detail(request, review_id):
    """
    GET: Obtiene detalles de una review
    PUT: Actualiza una review
    DELETE: Elimina una review
    """
    try:
        user_id = request.jwt_user_id
        review = get_object_or_404(Review, id=review_id)
        
        if request.method == 'GET':
            # Cualquiera puede ver reviews visibles
            if not review.is_visible:
                return Response(
                    {'error': 'Review no disponible'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = ReviewSerializer(review)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            # Solo el autor puede actualizar
            if review.reviewer_id != user_id:
                return Response(
                    {'error': 'Solo puedes actualizar tus propias reseñas'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = ReviewUpdateSerializer(review, data=request.data, partial=True)
            if serializer.is_valid():
                review = serializer.save()
                return Response(
                    ReviewSerializer(review).data,
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # Solo el autor puede eliminar
            if review.reviewer_id != user_id:
                return Response(
                    {'error': 'Solo puedes eliminar tus propias reseñas'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            review.delete()
            return Response(
                {'message': 'Review eliminada correctamente'},
                status=status.HTTP_204_NO_CONTENT
            )
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def service_reviews(request, service_id):
    """
    Lista reviews de un servicio específico (público)
    """
    try:
        service = get_object_or_404(Service, id=service_id, is_active=True, is_published=True)
        
        reviews = Review.objects.filter(
            service=service, 
            is_visible=True
        ).order_by('-created_at')
        
        # Filtros opcionales
        rating_filter = request.GET.get('rating')
        if rating_filter:
            reviews = reviews.filter(rating=rating_filter)
        
        serializer = ReviewSerializer(reviews, many=True)
        return Response({
            'reviews': serializer.data,
            'count': reviews.count(),
            'service': {
                'id': service.id,
                'title': service.title,
                'average_rating': service.rating_avg,
                'total_reviews': service.reviews_count
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def review_flag(request, review_id):
    """
    Reportar una review como inapropiada
    """
    try:
        user_id = request.jwt_user_id
        review = get_object_or_404(Review, id=review_id)
        
        # No se puede reportar la propia review
        if review.reviewer_id == user_id:
            return Response(
                {'error': 'No puedes reportar tu propia reseña'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'Contenido inapropiado')
        
        review.is_flagged = True
        review.flagged_reason = reason
        review.save()
        
        return Response(
            {'message': 'Review reportada correctamente'},
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ADMIN ENDPOINTS

@api_view(['GET'])
@jwt_required_drf
def admin_reviews_list(request):
    """
    Lista todas las reviews para moderación (solo admin)
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'ADMIN':
            return Response(
                {'error': 'Acceso denegado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Filtros
        flagged_only = request.GET.get('flagged') == 'true'
        
        reviews = Review.objects.all()
        if flagged_only:
            reviews = reviews.filter(is_flagged=True)
        
        reviews = reviews.order_by('-created_at')
        
        serializer = ReviewModerationSerializer(reviews, many=True)
        return Response({
            'reviews': serializer.data,
            'count': reviews.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@jwt_required_drf
def admin_review_moderate(request, review_id):
    """
    Moderar una review (solo admin)
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'ADMIN':
            return Response(
                {'error': 'Acceso denegado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        review = get_object_or_404(Review, id=review_id)
        
        serializer = ReviewModerationSerializer(
            review, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            review = serializer.save()
            return Response(
                ReviewModerationSerializer(review).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
