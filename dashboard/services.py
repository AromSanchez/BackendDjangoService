"""
Services para el módulo Dashboard
Contiene la lógica de negocio para generar datos según el rol
"""
from apps.users.models import User
from apps.services.models import Service
from apps.bookings.models import Booking
from apps.reviews.models import Review
from apps.favorites.models import Favorite
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta


class DashboardService:
    """
    Servicio que maneja la lógica del dashboard según el rol del usuario
    """
    
    @staticmethod
    def get_customer_data(user):
        """
        Genera datos del dashboard para un CUSTOMER
        
        Args:
            user: Instancia del modelo User
            
        Returns:
            dict: Datos específicos para clientes
        """
        try:
            # Consultas reales para el dashboard del cliente
            from datetime import datetime
            
            # Bookings del cliente
            bookings = Booking.objects.filter(customer_id=user.id)
            total_bookings = bookings.count()
            pending_bookings = bookings.filter(status='pending').count()
            completed_bookings = bookings.filter(status='completed').count()
            rejected_bookings = bookings.filter(
                status__in=['rejected', 'canceled_by_customer', 'canceled_by_provider']
            ).count()
            
            # Gasto total (solo de bookings completados)
            completed_bookings_qs = bookings.filter(status='completed')
            total_spent = sum(
                (booking.service_price if booking.service_price is not None else booking.service.price) 
                for booking in completed_bookings_qs
            )
            
            # Servicios destacados (servicios activos y publicados, limitados a 6)
            featured_services = []
            services = Service.objects.filter(
                is_active=True, 
                is_published=True
            ).order_by('-rating_avg', '-created_at')[:6]
            
            for service in services:
                featured_services.append({
                    'id': service.id,
                    'name': service.title,
                    'description': service.description,
                    'price': float(service.price),
                    'average_rating': float(service.rating_avg or 0),
                })
            
            # Mis solicitudes recientes (limitado a 5)
            recent_requests = []
            for booking in bookings.order_by('-created_at')[:5]:
                recent_requests.append({
                    'id': booking.id,
                    'service_name': booking.service.title,
                    'provider_name': booking.provider.full_name if booking.provider else "Proveedor",
                    'status': booking.status,
                    'created_at': booking.created_at
                })
            
            # Solicitudes rechazadas (limitado a 5)
            rejected_requests = []
            rejected_bookings_qs = bookings.filter(
                status__in=['rejected', 'canceled_by_customer', 'canceled_by_provider']
            ).order_by('-created_at')[:5]
            
            for booking in rejected_bookings_qs:
                rejected_requests.append({
                    'id': booking.id,
                    'service_name': booking.service.title,
                    'provider_name': booking.provider.full_name if booking.provider else "Proveedor",
                    'status': booking.status,
                    'created_at': booking.created_at,
                    'cancellation_reason': booking.cancellation_reason
                })
            
            return {
                "estadisticas": {
                    'total_bookings': total_bookings,
                    'pending_bookings': pending_bookings,
                    'completed_bookings': completed_bookings,
                    'rejected_bookings': rejected_bookings,
                    'total_spent': float(total_spent)
                },
                "serviciosDestacados": featured_services,
                "misSolicitudes": recent_requests,
                "solicitudesRechazadas": rejected_requests
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR CUSTOMER DATA: {str(e)}")
            return {
                "estadisticas": {
                    'total_bookings': 0,
                    'pending_bookings': 0,
                    'completed_bookings': 0,
                    'total_spent': 0
                },
                "serviciosDestacados": [],
                "misSolicitudes": []
            }
    
    @staticmethod
    def get_provider_data(user):
        """
        Genera datos del dashboard para un PROVIDER (versión simplificada)
        
        Args:
            user: Instancia del modelo User
            
        Returns:
            dict: Datos específicos para proveedores
        """
        # Datos básicos sin consultas complejas por ahora
        try:
            # Consultas reales para el dashboard
            from datetime import datetime
            
            # Servicios
            services = Service.objects.filter(provider_id=user.id)
            active_services = services.filter(is_active=True).count()
            
            # Bookings
            bookings = Booking.objects.filter(provider_id=user.id)
            pending_bookings = bookings.filter(status='pending').count()
            completed_bookings = bookings.filter(status='completed').count()
            
            # Ingresos
            completed_bookings_qs = bookings.filter(status='completed')
            total_revenue = sum(
                (booking.service_price if booking.service_price is not None else booking.service.price) 
                for booking in completed_bookings_qs
            )
            
            # Ingresos mensuales
            current_month = datetime.now().replace(day=1)
            current_month_revenue = sum(
                (booking.service_price if booking.service_price is not None else booking.service.price)
                for booking in bookings.filter(
                    created_at__gte=current_month,
                    status='completed'
                )
            )
            
            # Mes anterior
            last_month = (current_month - timedelta(days=1)).replace(day=1)
            last_month_revenue = sum(
                (booking.service_price if booking.service_price is not None else booking.service.price)
                for booking in bookings.filter(
                    created_at__gte=last_month,
                    created_at__lt=current_month,
                    status='completed'
                )
            )
            
            # Crecimiento
            growth = 0
            if last_month_revenue > 0:
                growth = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
            elif current_month_revenue > 0:
                growth = 100
                
            growth_str = f"{'+' if growth >= 0 else ''}{growth:.1f}%"

            # Mis Servicios (limitado a 5)
            my_services = []
            for service in services.order_by('-created_at')[:5]:
                my_services.append({
                    'id': service.id,
                    'name': service.title,
                    'description': service.description,
                    'price': float(service.price),
                    'average_rating': float(service.rating_avg or 0),
                    'request_count': service.bookings.count(),
                    'completion_count': service.bookings.filter(status='completed').count()
                })

            # Solicitudes Pendientes (limitado a 5)
            pending_requests = []
            for booking in bookings.filter(status='pending').order_by('-created_at')[:5]:
                pending_requests.append({
                    'id': booking.id,
                    'service_name': booking.service.title,
                    'customer_name': booking.customer.full_name if booking.customer else "Usuario eliminado",
                    'status': booking.status,
                    'created_at': booking.created_at
                })

            # Reviews
            reviews = Review.objects.filter(service__provider_id=user.id)
            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

            return {
                "estadisticas": {
                    'active_services': active_services,
                    'pending_bookings': pending_bookings,
                    'completed_bookings': completed_bookings,
                    'total_revenue': float(total_revenue),
                    'calificacion_promedio': float(avg_rating)
                },
                "ingresos_mensuales": {
                    'current_month': float(current_month_revenue),
                    'previous_month': float(last_month_revenue),
                    'growth': growth_str
                },
                "misServicios": my_services,
                "solicitudesPendientes": pending_requests
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR PROVIDER DATA: {str(e)}")
            return {
                "estadisticas": {
                    'active_services': 0,
                    'pending_bookings': 0,
                    'completed_bookings': 0,
                    'total_revenue': 0,
                    'calificacion_promedio': 0
                },
                "ingresos_mensuales": {
                    'current_month': 0,
                    'previous_month': 0,
                    'growth': "0%"
                },
                "misServicios": [],
                "solicitudesPendientes": []
            }
    
    @staticmethod
    def get_admin_data(user):
        """
        Genera datos del dashboard para un ADMIN (versión simplificada)
        """
        total_users = User.objects.count()
        customer_count = User.objects.filter(role='CUSTOMER').count()
        provider_count = User.objects.filter(role='PROVIDER').count()
        admin_count = User.objects.filter(role='ADMIN').count()

        total_services = Service.objects.count()
        active_services = Service.objects.filter(is_active=True, is_published=True).count()
        pending_services = Service.objects.filter(is_published=False).count()

        completed_bookings = Booking.objects.filter(status='completed')
        total_revenue = completed_bookings.aggregate(
            total=Sum('service__price')
        )['total'] or 0

        pending_providers = list(
            User.objects.filter(role='PROVIDER', provider_status='PENDING')
                .values('id', 'full_name', 'email', 'created_at')
        )

        return {
            "usuarios": {
                "total": total_users,
                "customers": customer_count,
                "providers": provider_count,
                "admins": admin_count
            },
            "servicios": {
                "total": total_services,
                "active": active_services,
                "pending": pending_services
            },
            "transacciones": {
                "total_revenue": float(total_revenue),
                "completed_bookings": completed_bookings.count()
            },
            "pending_providers": pending_providers
        }
    
    @staticmethod
    def get_dashboard_data(user):
        """
        Método principal que retorna los datos del dashboard según el rol
        
        Args:
            user: Instancia del modelo User
            
        Returns:
            dict: Respuesta completa del dashboard
        """
        # Determinar qué datos retornar según el rol
        if user.is_customer:
            data = DashboardService.get_customer_data(user)
            message = f"Bienvenido {user.full_name}, aquí están tus servicios disponibles"
        elif user.is_provider:
            data = DashboardService.get_provider_data(user)
            message = f"Bienvenido {user.full_name}, gestiona tus servicios y pedidos"
        elif user.is_admin:
            data = DashboardService.get_admin_data(user)
            message = f"Panel de administración - {user.full_name}"
        else:
            data = {}
            message = "Rol no reconocido"
        
        return {
            "role": user.role,
            "user": user,
            "data": data,
            "message": message
        }
