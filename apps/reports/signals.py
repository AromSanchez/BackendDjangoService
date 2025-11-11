"""
Signals para reportes
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Report
from apps.shared.springboot_client import SpringBootClient


@receiver(post_save, sender=Report)
def on_report_status_change(sender, instance, created, **kwargs):
    """
    Sincronizar reportes con Spring Boot
    """
    if created:
        # Nuevo reporte - actualizar reputación del reportado
        if instance.reported_user_id:
            SpringBootClient.update_reputation(
                user_id=instance.reported_user_id,
                action='report_received'
            )
    
    elif instance.status == 'resolved' and instance.resolved_at:
        # Reporte resuelto - notificar al reportador
        SpringBootClient.create_notification(
            user_id=instance.reporter_id,
            notification_type='REPORT_RESOLVED',
            title='Reporte resuelto',
            message='Tu reporte ha sido revisado y resuelto',
            link_url=f'/reports/{instance.id}',
            related_id=instance.id
        )
