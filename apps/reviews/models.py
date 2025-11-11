"""
Modelos de reseñas
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.services.models import Service
from apps.bookings.models import Booking
from apps.users.models import User


class Review(models.Model):
    """
    Reseñas de servicios (solo clientes pueden dejar reseñas)
    """
    reviewer_id = models.BigIntegerField(db_index=True)  # Cliente
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, null=True, blank=True)
    
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True, max_length=1000)
    
    # Moderación
    is_visible = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    flagged_reason = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews'
        indexes = [
            models.Index(fields=['service', '-created_at']),
            models.Index(fields=['reviewer_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['booking'],
                name='unique_review_per_booking'
            )
        ]
    
    @property
    def reviewer(self):
        try:
            return User.objects.get(id=self.reviewer_id)
        except User.DoesNotExist:
            return None
