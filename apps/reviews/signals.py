"""
Signals para sincronización automática de reviews
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review
from apps.services.models import Service
from apps.shared.springboot_client import SpringBootClient


@receiver(post_save, sender=Review)
def on_review_created_or_updated(sender, instance, created, **kwargs):
    """
    Cuando se crea o actualiza una review:
    1. Actualizar rating del Service
    2. Actualizar reputación del proveedor en Spring Boot
    3. Notificar al proveedor
    """
    # Actualizar rating del servicio
    service = instance.service
    reviews = service.reviews.filter(is_visible=True)
    service.reviews_count = reviews.count()
    service.rating_sum = sum(r.rating for r in reviews)
    service.rating_avg = service.rating_sum / service.reviews_count if service.reviews_count > 0 else 0
    service.save(update_fields=['reviews_count', 'rating_sum', 'rating_avg'])
    
    if created:
        # Actualizar reputación del proveedor en Spring Boot
        SpringBootClient.update_reputation(
            user_id=service.provider_id,
            action='review_received',
            rating=instance.rating
        )
        
        # Notificar al proveedor
        SpringBootClient.create_notification(
            user_id=service.provider_id,
            notification_type='REVIEW_RECEIVED',
            title='Nueva reseña recibida',
            message=f'Recibiste una reseña de {instance.rating} estrellas en "{service.title}"',
            link_url=f'/services/{service.id}/reviews',
            related_id=instance.id
        )


@receiver(post_delete, sender=Review)
def on_review_deleted(sender, instance, **kwargs):
    """
    Recalcular rating cuando se elimina una review
    """
    service = instance.service
    reviews = service.reviews.filter(is_visible=True)
    service.reviews_count = reviews.count()
    service.rating_sum = sum(r.rating for r in reviews)
    service.rating_avg = service.rating_sum / service.reviews_count if service.reviews_count > 0 else 0
    service.save(update_fields=['reviews_count', 'rating_sum', 'rating_avg'])
