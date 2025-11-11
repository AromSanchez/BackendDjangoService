"""
Modelos de favoritos
"""
from django.db import models
from apps.services.models import Service


class Favorite(models.Model):
    """
    Servicios favoritos de usuarios
    """
    user_id = models.BigIntegerField(db_index=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'favorites'
        unique_together = ('user_id', 'service')
        indexes = [
            models.Index(fields=['user_id', '-created_at']),
        ]
