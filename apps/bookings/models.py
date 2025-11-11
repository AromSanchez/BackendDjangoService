"""
Modelos de reservas/bookings
"""
from django.db import models
from apps.services.models import Service
from apps.users.models import User


class Booking(models.Model):
    """
    Reservas/Solicitudes de servicio
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('negotiating', 'En Negociación'),
        ('accepted', 'Aceptado'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('canceled_by_customer', 'Cancelado por Cliente'),
        ('canceled_by_provider', 'Cancelado por Proveedor'),
        ('rejected', 'Rechazado'),
    ]
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    customer_id = models.BigIntegerField(db_index=True)
    provider_id = models.BigIntegerField(db_index=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    
    # Detalles
    booking_date = models.DateField(null=True, blank=True)
    booking_time = models.TimeField(null=True, blank=True)
    booking_notes = models.TextField(blank=True, null=True)
    customer_address = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps de estados
    accepted_at = models.DateTimeField(null=True, blank=True)
    in_progress_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bookings'
        indexes = [
            models.Index(fields=['customer_id', 'status']),
            models.Index(fields=['provider_id', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    @property
    def customer(self):
        try:
            return User.objects.get(id=self.customer_id)
        except User.DoesNotExist:
            return None
    
    @property
    def provider(self):
        try:
            return User.objects.get(id=self.provider_id)
        except User.DoesNotExist:
            return None
