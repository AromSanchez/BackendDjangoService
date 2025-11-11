"""
Signals para sincronización automática de bookings
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Booking
from apps.shared.springboot_client import SpringBootClient


@receiver(post_save, sender=Booking)
def on_booking_status_change(sender, instance, created, **kwargs):
    """
    Sincronizar con Spring Boot cuando cambia el estado de un booking
    """
    if created:
        # Nuevo booking creado - notificar al proveedor
        SpringBootClient.create_notification(
            user_id=instance.provider_id,
            notification_type='BOOKING_REQUEST',
            title='Nueva solicitud de servicio',
            message=f'Tienes una nueva solicitud para: {instance.service.title}',
            link_url=f'/bookings/{instance.id}',
            related_id=instance.id
        )
    
    elif instance.status == 'accepted':
        # Booking aceptado - notificar al cliente
        SpringBootClient.create_notification(
            user_id=instance.customer_id,
            notification_type='BOOKING_ACCEPTED',
            title='Solicitud aceptada',
            message=f'Tu solicitud para "{instance.service.title}" fue aceptada',
            link_url=f'/bookings/{instance.id}',
            related_id=instance.id
        )
    
    elif instance.status == 'rejected':
        # Booking rechazado - notificar al cliente
        SpringBootClient.create_notification(
            user_id=instance.customer_id,
            notification_type='BOOKING_REJECTED',
            title='Solicitud rechazada',
            message=f'Tu solicitud para "{instance.service.title}" fue rechazada',
            link_url=f'/bookings/{instance.id}',
            related_id=instance.id
        )
    
    elif instance.status == 'completed':
        # Booking completado - actualizar reputación de ambos usuarios
        SpringBootClient.update_reputation(
            user_id=instance.provider_id,
            action='service_completed'
        )
        SpringBootClient.update_reputation(
            user_id=instance.customer_id,
            action='booking_completed'
        )
        
        # Notificar a ambos
        SpringBootClient.create_notification(
            user_id=instance.provider_id,
            notification_type='BOOKING_COMPLETED',
            title='Servicio completado',
            message=f'El servicio "{instance.service.title}" ha sido completado',
            link_url=f'/bookings/{instance.id}',
            related_id=instance.id
        )
        SpringBootClient.create_notification(
            user_id=instance.customer_id,
            notification_type='BOOKING_COMPLETED',
            title='Servicio completado',
            message=f'¿Qué tal fue tu experiencia con "{instance.service.title}"? Deja tu reseña',
            link_url=f'/bookings/{instance.id}/review',
            related_id=instance.id
        )
    
    elif instance.status in ['canceled_by_customer', 'canceled_by_provider']:
        # Booking cancelado - actualizar reputación negativamente
        if instance.status == 'canceled_by_provider':
            SpringBootClient.update_reputation(
                user_id=instance.provider_id,
                action='service_canceled'
            )
            # Notificar al cliente
            SpringBootClient.create_notification(
                user_id=instance.customer_id,
                notification_type='BOOKING_CANCELED',
                title='Servicio cancelado',
                message=f'El proveedor canceló el servicio "{instance.service.title}"',
                link_url=f'/bookings/{instance.id}',
                related_id=instance.id
            )
        else:
            SpringBootClient.update_reputation(
                user_id=instance.customer_id,
                action='booking_canceled'
            )
            # Notificar al proveedor
            SpringBootClient.create_notification(
                user_id=instance.provider_id,
                notification_type='BOOKING_CANCELED',
                title='Servicio cancelado',
                message=f'El cliente canceló la solicitud para "{instance.service.title}"',
                link_url=f'/bookings/{instance.id}',
                related_id=instance.id
            )
