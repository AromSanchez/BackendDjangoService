"""
Views para el módulo de users
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone

from conectaya.authentication.decorators import jwt_required_drf
from .models import User, UserProfile
from .serializers import (
    UserSerializer, UserProfileSerializer, UserProfileCreateSerializer,
    UserProfileUpdateSerializer, UserProfilePublicSerializer,
    UserListSerializer, UserAdminSerializer
)


@api_view(['GET', 'PUT'])
@jwt_required_drf
def user_profile(request):
    """
    GET: Obtiene perfil del usuario autenticado
    PUT: Actualiza perfil del usuario autenticado
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if request.method == 'GET':
            # Obtener o crear perfil
            profile, created = UserProfile.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'bio': '',
                    'city': '',
                    'country': 'Perú'
                }
            )
            
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            # Actualizar perfil
            profile, created = UserProfile.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'bio': '',
                    'city': '',
                    'country': 'Perú'
                }
            )
            
            serializer = UserProfileUpdateSerializer(
                profile, 
                data=request.data, 
                partial=True
            )
            
            if serializer.is_valid():
                profile = serializer.save()
                return Response(
                    UserProfileSerializer(profile).data,
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def user_profile_public(request, user_id):
    """
    Obtiene perfil público de un usuario
    """
    try:
        user = get_object_or_404(User, id=user_id, is_active=True)
        
        try:
            profile = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            # Crear perfil básico si no existe
            profile = UserProfile.objects.create(
                user_id=user_id,
                bio='',
                city='',
                country='Perú'
            )
            
        serializer = UserProfilePublicSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def user_info(request):
    """
    Obtiene información básica del usuario autenticado
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ADMIN ENDPOINTS

@api_view(['GET'])
@jwt_required_drf
def admin_users_list(request):
    """
    Lista todos los usuarios (solo admin)
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
        role_filter = request.GET.get('role')
        status_filter = request.GET.get('status')
        provider_status_filter = request.GET.get('provider_status')
        search_query = request.GET.get('search')
        
        users = User.objects.all()
        
        if role_filter:
            users = users.filter(role=role_filter)
        
        if status_filter:
            normalized_status = status_filter.lower()
            if normalized_status == 'active':
                users = users.filter(is_active=True)
            elif normalized_status in ['inactive', 'suspended']:
                users = users.filter(is_active=False)

        if provider_status_filter:
            users = users.filter(provider_status=provider_status_filter)

        if search_query:
            users = users.filter(
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            )
        
        users = users.order_by('-created_at')
        total_filtered = users.count()

        today = timezone.localdate()
        summary = {
            'total': total_filtered,
            'customers': users.filter(role='CUSTOMER').count(),
            'providers': users.filter(role='PROVIDER').count(),
            'admins': users.filter(role='ADMIN').count(),
            'active': users.filter(is_active=True).count(),
            'inactive': users.filter(is_active=False).count(),
            'pending_providers': users.filter(role='PROVIDER', provider_status='PENDING').count(),
            'new_today': users.filter(created_at__date=today).count()
        }

        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('page_size') or 15)
        paginated_users = paginator.paginate_queryset(users, request)
        serializer = UserListSerializer(paginated_users, many=True)

        return Response({
            'count': total_filtered,
            'page': paginator.page.number,
            'page_size': paginator.get_page_size(request),
            'total_pages': paginator.page.paginator.num_pages,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': serializer.data,
            'summary': summary
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT'])
@jwt_required_drf
def admin_user_detail(request, target_user_id):
    """
    GET: Obtiene detalles de un usuario (solo admin)
    PUT: Actualiza un usuario (solo admin)
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'ADMIN':
            return Response(
                {'error': 'Acceso denegado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        target_user = get_object_or_404(User, id=target_user_id)
        
        if request.method == 'GET':
            serializer = UserAdminSerializer(target_user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            serializer = UserAdminSerializer(
                target_user, 
                data=request.data, 
                partial=True
            )
            
            if serializer.is_valid():
                target_user = serializer.save()
                return Response(
                    UserAdminSerializer(target_user).data,
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def admin_user_toggle_status(request, target_user_id):
    """
    Activar/desactivar usuario (solo admin)
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'ADMIN':
            return Response(
                {'error': 'Acceso denegado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        target_user = get_object_or_404(User, id=target_user_id)
        
        # No se puede desactivar a sí mismo
        if target_user_id == user_id:
            return Response(
                {'error': 'No puedes desactivar tu propia cuenta'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # No se puede desactivar a otros admins
        if target_user.role == 'ADMIN':
            return Response(
                {'error': 'No puedes desactivar otros administradores'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        target_user.is_active = not target_user.is_active
        target_user.save()
        
        action = 'activado' if target_user.is_active else 'desactivado'
        
        return Response({
            'message': f'Usuario {action} correctamente',
            'user': UserAdminSerializer(target_user).data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def admin_users_stats(request):
    """
    Estadísticas de usuarios (solo admin)
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'ADMIN':
            return Response(
                {'error': 'Acceso denegado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.db.models import Count
        
        # Estadísticas generales
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
        
        # Por rol
        customers = User.objects.filter(role='CUSTOMER').count()
        providers = User.objects.filter(role='PROVIDER').count()
        admins = User.objects.filter(role='ADMIN').count()
        
        # Proveedores por estado
        pending_providers = User.objects.filter(
            role='PROVIDER', 
            provider_status='PENDING'
        ).count()
        approved_providers = User.objects.filter(
            role='PROVIDER', 
            provider_status='APPROVED'
        ).count()
        rejected_providers = User.objects.filter(
            role='PROVIDER', 
            provider_status='REJECTED'
        ).count()
        
        # Usuarios recientes (últimos 30 días)
        from datetime import datetime, timedelta
        month_ago = datetime.now() - timedelta(days=30)
        
        recent_users = User.objects.filter(
            created_at__gte=month_ago
        ).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'customers': customers,
            'providers': providers,
            'admins': admins,
            'pending_providers': pending_providers,
            'approved_providers': approved_providers,
            'rejected_providers': rejected_providers,
            'recent_users': recent_users
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def user_upload_avatar(request):
    """
    Subir avatar del usuario (placeholder - requiere integración con Spring Boot)
    """
    try:
        user_id = request.jwt_user_id
        
        file_id = request.data.get('file_id')
        if not file_id:
            return Response(
                {'error': 'file_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener o crear perfil
        profile, created = UserProfile.objects.get_or_create(
            user_id=user_id,
            defaults={
                'bio': '',
                'city': '',
                'country': 'Perú'
            }
        )
        
        profile.avatar_file_id = file_id
        profile.save()
        
        return Response(
            UserProfileSerializer(profile).data,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@jwt_required_drf
def user_update_notifications(request):
    """
    Actualizar configuración de notificaciones
    """
    try:
        user_id = request.jwt_user_id
        
        # Obtener o crear perfil
        profile, created = UserProfile.objects.get_or_create(
            user_id=user_id,
            defaults={
                'bio': '',
                'city': '',
                'country': 'Perú'
            }
        )
        
        # Actualizar configuraciones de notificación
        notification_email = request.data.get('notification_email')
        notification_push = request.data.get('notification_push')
        
        if notification_email is not None:
            profile.notification_email = notification_email
        
        if notification_push is not None:
            profile.notification_push = notification_push
        
        profile.save()
        
        return Response(
            UserProfileSerializer(profile).data,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def user_activity_summary(request):
    """
    Resumen de actividad del usuario
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        from apps.services.models import Service
        from apps.bookings.models import Booking
        from apps.reviews.models import Review
        from apps.favorites.models import Favorite
        
        summary = {
            'user_info': {
                'id': user.id,
                'full_name': user.full_name,
                'role': user.role,
                'member_since': user.created_at
            }
        }
        
        if user.role == 'CUSTOMER':
            # Actividad como cliente
            total_bookings = Booking.objects.filter(customer_id=user_id).count()
            total_reviews = Review.objects.filter(reviewer_id=user_id).count()
            total_favorites = Favorite.objects.filter(user_id=user_id).count()
            
            summary['activity'] = {
                'total_bookings': total_bookings,
                'total_reviews': total_reviews,
                'total_favorites': total_favorites
            }
            
        elif user.role == 'PROVIDER':
            # Actividad como proveedor
            total_services = Service.objects.filter(provider_id=user_id).count()
            total_bookings = Booking.objects.filter(provider_id=user_id).count()
            total_reviews_received = Review.objects.filter(
                service__provider_id=user_id
            ).count()
            
            # Rating promedio
            services = Service.objects.filter(provider_id=user_id)
            avg_rating = sum(s.rating_avg for s in services) / len(services) if services else 0
            
            summary['activity'] = {
                'total_services': total_services,
                'total_bookings': total_bookings,
                'total_reviews_received': total_reviews_received,
                'average_rating': round(avg_rating, 2)
            }
        
        return Response(summary, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
