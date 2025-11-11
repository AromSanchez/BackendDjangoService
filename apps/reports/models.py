"""
Modelos de reportes
"""
from django.db import models
from apps.bookings.models import Booking
from apps.services.models import Service


class Report(models.Model):
    """
    Reportes de usuarios o servicios
    """
    STATUS_CHOICES = [
        ('open', 'Abierto'),
        ('in_review', 'En Revisión'),
        ('resolved', 'Resuelto'),
        ('dismissed', 'Desestimado'),
    ]
    
    REASON_CHOICES = [
        ('inappropriate_content', 'Contenido Inapropiado'),
        ('fraud', 'Fraude'),
        ('spam', 'Spam'),
        ('harassment', 'Acoso'),
        ('poor_service', 'Mal Servicio'),
        ('other', 'Otro'),
    ]
    
    reporter_id = models.BigIntegerField(db_index=True)
    reported_user_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Admin review
    admin_user_id = models.BigIntegerField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reports'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['reporter_id']),
            models.Index(fields=['reported_user_id']),
        ]
