"""
Services para el módulo Dashboard
Contiene la lógica de negocio para generar datos según el rol
"""
from .models import User


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
        return {
            "productos_destacados": [
                {
                    "id": 1,
                    "nombre": "Servicio de Limpieza",
                    "precio": 50.00,
                    "categoria": "Hogar"
                },
                {
                    "id": 2,
                    "nombre": "Reparación de PC",
                    "precio": 80.00,
                    "categoria": "Tecnología"
                },
                {
                    "id": 3,
                    "nombre": "Plomería Express",
                    "precio": 60.00,
                    "categoria": "Hogar"
                }
            ],
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
        Genera datos del dashboard para un PROVIDER
        
        Args:
            user: Instancia del modelo User
            
        Returns:
            dict: Datos específicos para proveedores
        """
        return {
            "mis_servicios": [
                {
                    "id": 1,
                    "nombre": "Limpieza Profesional",
                    "precio": 50.00,
                    "activo": True,
                    "calificacion": 4.8,
                    "total_ventas": 45
                },
                {
                    "id": 2,
                    "nombre": "Mantenimiento de Jardines",
                    "precio": 70.00,
                    "activo": True,
                    "calificacion": 4.9,
                    "total_ventas": 32
                }
            ],
            "pedidos_pendientes": [
                {
                    "id": 201,
                    "cliente": "Juan Pérez",
                    "servicio": "Limpieza Profesional",
                    "fecha_solicitud": "2024-11-05",
                    "estado": "Pendiente",
                    "monto": 50.00
                },
                {
                    "id": 202,
                    "cliente": "María García",
                    "servicio": "Mantenimiento de Jardines",
                    "fecha_solicitud": "2024-11-06",
                    "estado": "En proceso",
                    "monto": 70.00
                }
            ],
            "ingresos_mensuales": {
                "mes_actual": 1250.00,
                "mes_anterior": 980.00,
                "crecimiento": "+27.5%"
            },
            "estadisticas": {
                "servicios_activos": 2,
                "pedidos_completados": 77,
                "pedidos_pendientes": 2,
                "calificacion_promedio": 4.85,
                "ingresos_totales": 5430.00
            },
            "notificaciones": [
                {
                    "tipo": "nuevo_pedido",
                    "mensaje": "Tienes 2 nuevos pedidos pendientes",
                    "fecha": "2024-11-06"
                }
            ]
        }
    
    @staticmethod
    def get_admin_data(user):
        """
        Genera datos del dashboard para un ADMIN
        
        Args:
            user: Instancia del modelo User
            
        Returns:
            dict: Datos específicos para administradores
        """
        return {
            "usuarios": {
                "total": 1250,
                "clientes": 980,
                "proveedores": 245,
                "admins": 25,
                "nuevos_hoy": 15,
                "activos": 1180
            },
            "servicios": {
                "total": 450,
                "activos": 398,
                "pendientes_aprobacion": 12,
                "categorias": [
                    {"nombre": "Hogar", "cantidad": 180},
                    {"nombre": "Tecnología", "cantidad": 95},
                    {"nombre": "Construcción", "cantidad": 75},
                    {"nombre": "Educación", "cantidad": 60},
                    {"nombre": "Otros", "cantidad": 40}
                ]
            },
            "transacciones": {
                "total_mes": 45680.00,
                "total_dia": 1250.00,
                "pendientes": 15,
                "completadas_hoy": 45
            },
            "reportes": {
                "ingresos_mensuales": [
                    {"mes": "Enero", "monto": 35000},
                    {"mes": "Febrero", "monto": 38000},
                    {"mes": "Marzo", "monto": 42000},
                    {"mes": "Abril", "monto": 45000},
                    {"mes": "Mayo", "monto": 45680}
                ],
                "servicios_mas_solicitados": [
                    {"servicio": "Limpieza", "cantidad": 450},
                    {"servicio": "Plomería", "cantidad": 320},
                    {"servicio": "Electricidad", "cantidad": 280}
                ]
            },
            "alertas": [
                {
                    "tipo": "warning",
                    "mensaje": "12 servicios pendientes de aprobación",
                    "prioridad": "media"
                },
                {
                    "tipo": "info",
                    "mensaje": "15 nuevos usuarios registrados hoy",
                    "prioridad": "baja"
                }
            ],
            "proveedores_pendientes_verificacion": [
                {
                    "id": 301,
                    "nombre": "Carlos Rodríguez",
                    "email": "carlos@example.com",
                    "fecha_solicitud": "2024-11-05",
                    "servicios_propuestos": 3
                }
            ]
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
