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
        Genera datos del dashboard para un CUSTOMER (versión simplificada)
        
        Args:
            user: Instancia del modelo User
            
        Returns:
            dict: Datos específicos para clientes
        """
        # Datos básicos sin consultas complejas por ahora
        return {
            "estadisticas": {
                'total_bookings': 0,
                'pending_bookings': 0,
                'completed_bookings': 0,
                'total_spent': 0
            },
            "serviciosDestacados": [],
            "misSolicitudes": [],
            "ofertas_especiales": [
                {
                    "id": 1,
                    "titulo": "20% OFF en servicios de hogar",
                    "descripcion": "Descuento en todos los servicios de limpieza",
                    "descuento": "20%",
                    "valido_hasta": "2024-12-31"
                },
                {
                    "id": 2,
                    "titulo": "Primera consulta gratis",
                    "descripcion": "Para nuevos clientes en servicios técnicos",
                    "descuento": "100%",
                    "valido_hasta": "2024-11-30"
                }
            ],
            "mis_pedidos_recientes": [
                {
                    "id": 101,
                    "servicio": "Limpieza de hogar",
                    "fecha": "2024-11-01",
                    "estado": "Completado",
                    "total": 50.00
                }
            ],
            "estadisticas": {
                "pedidos_totales": 5,
                "pedidos_pendientes": 1,
                "pedidos_completados": 4,
                "gasto_total": 350.00
            }
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
        return {
            "estadisticas": {
                'active_services': 0,
                'pending_bookings': 0,
                'completed_bookings': 0,
                'total_revenue': 0
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
        
        Args:
            user: Instancia del modelo User
            
        Returns:
            dict: Datos específicos para administradores
        """
        # Datos básicos sin consultas complejas por ahora
        return {
            "usuarios": {
                "total": 0,
                "customers": 0,
                "providers": 0,
                "admins": 0
            },
            "servicios": {
                "total": 0,
                "active": 0,
                "pending": 0
            },
            "transacciones": {
                "total_revenue": 0,
                "completed_bookings": 0
            },
            "pending_providers": []
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
