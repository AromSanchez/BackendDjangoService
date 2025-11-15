"""
Views para el módulo Dashboard
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from conectaya.authentication.decorators import jwt_required_drf
from apps.users.models import User
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


@api_view(['GET'])
@jwt_required_drf
def provider_stats(request):
    """
    Estadísticas detalladas para proveedores
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'PROVIDER':
            return Response(
                {'error': 'Solo los proveedores pueden acceder a estas estadísticas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from apps.services.models import Service
        from apps.bookings.models import Booking
        from apps.reviews.models import Review
        from datetime import datetime, timedelta
        from django.db.models import Count, Avg, Sum
        
        # Servicios
        services = Service.objects.filter(provider_id=user_id)
        total_services = services.count()
        active_services = services.filter(is_active=True).count()
        published_services = services.filter(is_published=True).count()
        
        # Bookings
        bookings = Booking.objects.filter(provider_id=user_id)
        total_bookings = bookings.count()
        pending_bookings = bookings.filter(status='pending').count()
        completed_bookings = bookings.filter(status='completed').count()
        
        # Reviews
        reviews = Review.objects.filter(service__provider_id=user_id)
        total_reviews = reviews.count()
        avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        
        # Ingresos (estimados)
        completed_bookings_qs = bookings.filter(status='completed')
        total_revenue = sum(booking.service.price for booking in completed_bookings_qs)
        
        # Estadísticas del mes actual
        current_month = datetime.now().replace(day=1)
        monthly_bookings = bookings.filter(
            created_at__gte=current_month,
            status='completed'
        ).count()
        
        monthly_revenue = sum(
            booking.service.price for booking in bookings.filter(
                created_at__gte=current_month,
                status='completed'
            )
        )
        
        # Tendencias (últimos 6 meses)
        months_data = []
        for i in range(6):
            month_start = (datetime.now().replace(day=1) - timedelta(days=30*i))
            month_end = month_start.replace(day=28) + timedelta(days=4)
            
            month_bookings = bookings.filter(
                created_at__gte=month_start,
                created_at__lt=month_end,
                status='completed'
            ).count()
            
            month_revenue = sum(
                booking.service.price for booking in bookings.filter(
                    created_at__gte=month_start,
                    created_at__lt=month_end,
                    status='completed'
                )
            )
            
            months_data.append({
                'month': month_start.strftime('%Y-%m'),
                'bookings': month_bookings,
                'revenue': float(month_revenue)
            })
        
        from dashboard.serializers import ProviderStatsSerializer
        
        stats_data = {
            'total_services': total_services,
            'active_services': active_services,
            'published_services': published_services,
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'completed_bookings': completed_bookings,
            'total_reviews': total_reviews,
            'average_rating': round(float(avg_rating), 2),
            'total_revenue': float(total_revenue),
            'this_month_revenue': float(monthly_revenue),
            'bookings_by_month': months_data,
            'revenue_by_month': months_data
        }
        
        serializer = ProviderStatsSerializer(stats_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def customer_stats(request):
    """
    Estadísticas detalladas para clientes
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'CUSTOMER':
            return Response(
                {'error': 'Solo los clientes pueden acceder a estas estadísticas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from apps.bookings.models import Booking
        from apps.reviews.models import Review
        from apps.favorites.models import Favorite
        from datetime import datetime, timedelta
        from django.db.models import Count
        
        # Bookings
        bookings = Booking.objects.filter(customer_id=user_id)
        total_bookings = bookings.count()
        pending_bookings = bookings.filter(status='pending').count()
        completed_bookings = bookings.filter(status='completed').count()
        
        # Reviews
        reviews = Review.objects.filter(reviewer_id=user_id)
        total_reviews = reviews.count()
        
        # Favoritos
        favorites = Favorite.objects.filter(user_id=user_id)
        total_favorites = favorites.count()
        
        # Gastos (estimados)
        completed_bookings_qs = bookings.filter(status='completed')
        total_spent = sum(booking.service.price for booking in completed_bookings_qs)
        
        # Gastos del mes actual
        current_month = datetime.now().replace(day=1)
        monthly_spent = sum(
            booking.service.price for booking in bookings.filter(
                created_at__gte=current_month,
                status='completed'
            )
        )
        
        # Categorías más utilizadas
        top_categories = bookings.filter(
            status='completed'
        ).values(
            'service__category__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Bookings recientes
        recent_bookings = bookings.order_by('-created_at')[:5]
        recent_bookings_data = []
        for booking in recent_bookings:
            recent_bookings_data.append({
                'id': booking.id,
                'service_title': booking.service.title,
                'status': booking.status,
                'created_at': booking.created_at,
                'price': float(booking.service.price)
            })
        
        from dashboard.serializers import CustomerStatsSerializer
        
        stats_data = {
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'completed_bookings': completed_bookings,
            'total_reviews': total_reviews,
            'total_favorites': total_favorites,
            'total_spent': float(total_spent),
            'this_month_spent': float(monthly_spent),
            'top_categories': list(top_categories),
            'recent_bookings': recent_bookings_data
        }
        
        serializer = CustomerStatsSerializer(stats_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def admin_stats(request):
    """
    Estadísticas detalladas para administradores
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if user.role != 'ADMIN':
            return Response(
                {'error': 'Solo los administradores pueden acceder a estas estadísticas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from apps.services.models import Service
        from apps.bookings.models import Booking
        from apps.reviews.models import Review
        from apps.reports.models import Report
        from datetime import datetime, timedelta
        from django.db.models import Count
        
        # Usuarios
        total_users = User.objects.count()
        total_customers = User.objects.filter(role='CUSTOMER').count()
        total_providers = User.objects.filter(role='PROVIDER').count()
        pending_providers = User.objects.filter(
            role='PROVIDER', 
            provider_status='PENDING'
        ).count()
        
        # Servicios
        total_services = Service.objects.count()
        published_services = Service.objects.filter(is_published=True).count()
        pending_services = Service.objects.filter(is_published=False).count()
        
        # Bookings
        total_bookings = Booking.objects.count()
        completed_bookings = Booking.objects.filter(status='completed').count()
        
        # Reviews y reportes
        total_reviews = Review.objects.count()
        flagged_reviews = Review.objects.filter(is_flagged=True).count()
        open_reports = Report.objects.filter(status='open').count()
        
        # Ingresos de la plataforma (estimado - comisión del 10%)
        completed_bookings_qs = Booking.objects.filter(status='completed')
        total_revenue = sum(booking.service.price for booking in completed_bookings_qs)
        platform_revenue = total_revenue * 0.10  # 10% de comisión
        
        # Tendencias de crecimiento (últimos 6 meses)
        months_data = []
        for i in range(6):
            month_start = (datetime.now().replace(day=1) - timedelta(days=30*i))
            month_end = month_start.replace(day=28) + timedelta(days=4)
            
            month_users = User.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            
            month_bookings = Booking.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            
            month_revenue = sum(
                booking.service.price for booking in Booking.objects.filter(
                    created_at__gte=month_start,
                    created_at__lt=month_end,
                    status='completed'
                )
            ) * 0.10
            
            months_data.append({
                'month': month_start.strftime('%Y-%m'),
                'users': month_users,
                'bookings': month_bookings,
                'revenue': float(month_revenue)
            })
        
        from dashboard.serializers import AdminStatsSerializer
        
        stats_data = {
            'total_users': total_users,
            'total_customers': total_customers,
            'total_providers': total_providers,
            'pending_providers': pending_providers,
            'total_services': total_services,
            'published_services': published_services,
            'pending_services': pending_services,
            'total_bookings': total_bookings,
            'completed_bookings': completed_bookings,
            'total_reviews': total_reviews,
            'flagged_reviews': flagged_reviews,
            'open_reports': open_reports,
            'platform_revenue': float(platform_revenue),
            'users_growth': months_data,
            'bookings_growth': months_data,
            'revenue_growth': months_data
        }
        
        serializer = AdminStatsSerializer(stats_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
