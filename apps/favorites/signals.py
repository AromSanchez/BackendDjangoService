"""
Signals para favoritos
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Favorite


@receiver(post_save, sender=Favorite)
def on_favorite_added(sender, instance, created, **kwargs):
    """
    Incrementar contador de favoritos
    """
    if created:
        service = instance.service
        service.favorites_count = service.favorites.count()
        service.save(update_fields=['favorites_count'])


@receiver(post_delete, sender=Favorite)
def on_favorite_removed(sender, instance, **kwargs):
    """
    Decrementar contador de favoritos
    """
    service = instance.service
    service.favorites_count = service.favorites.count()
    service.save(update_fields=['favorites_count'])
