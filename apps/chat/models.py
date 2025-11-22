"""
Modelos de chat
"""
from django.db import models
from apps.bookings.models import Booking
from apps.users.models import User


class Conversation(models.Model):
    """
    Conversación de chat (una por booking)
    """
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='conversation')
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'conversations'
        indexes = [
            models.Index(fields=['-last_message_at']),
        ]


class ConversationParticipant(models.Model):
    """
    Participantes de una conversación
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    user_id = models.BigIntegerField(db_index=True)
    unread_count = models.IntegerField(default=0)
    last_read_at = models.DateTimeField(null=True, blank=True)
    cleared_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'conversation_participants'
        unique_together = ('conversation', 'user_id')
        indexes = [
            models.Index(fields=['user_id']),
        ]
    
    @property
    def user(self):
        try:
            return User.objects.get(id=self.user_id)
        except User.DoesNotExist:
            return None


class Message(models.Model):
    """
    Mensajes de chat
    """
    MESSAGE_TYPES = [
        ('text', 'Texto'),
        ('image', 'Imagen'),
        ('file', 'Archivo'),
        ('system', 'Sistema'),
        ('booking_action', 'Acción de Reserva'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender_id = models.BigIntegerField(db_index=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(blank=True, null=True)
    file_id = models.BigIntegerField(null=True, blank=True)
    
    # Para mensajes de tipo booking_action
    booking_action = models.CharField(max_length=50, blank=True, null=True)
    # Valores posibles: request_acceptance, accept, reject, mark_complete, confirm_complete, cancel
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['sender_id']),
        ]
    
    @property
    def sender(self):
        try:
            return User.objects.get(id=self.sender_id)
        except User.DoesNotExist:
            return None
