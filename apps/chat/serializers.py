"""
Serializers para el módulo de chat
"""
from rest_framework import serializers
from .models import Conversation, ConversationParticipant, Message
from apps.bookings.models import Booking
from apps.users.models import User


class UserBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para usuarios en chat"""
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'role']


class BookingBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para booking en conversaciones"""
    
    service_title = serializers.CharField(source='service.title', read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'service_title', 'status', 'created_at']


class ConversationParticipantSerializer(serializers.ModelSerializer):
    """Serializer para participantes de conversación"""
    
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = [
            'id', 'user_id', 'user', 'unread_count', 'last_read_at'
        ]
        read_only_fields = ['id', 'unread_count', 'last_read_at']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer completo para mensajes"""
    
    sender = UserBasicSerializer(read_only=True)
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender_id', 'sender', 'message_type',
            'message_type_display', 'content', 'file_id', 'booking_action',
            'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'sender_id', 'is_read', 'created_at']
    
    def validate(self, data):
        """Validaciones personalizadas"""
        message_type = data.get('message_type', 'text')
        content = data.get('content')
        file_id = data.get('file_id')
        booking_action = data.get('booking_action')
        
        # Validar según el tipo de mensaje
        if message_type == 'text' and not content:
            raise serializers.ValidationError("Los mensajes de texto requieren contenido")
        
        if message_type in ['image', 'file'] and not file_id:
            raise serializers.ValidationError("Los mensajes de archivo requieren file_id")
        
        if message_type == 'booking_action' and not booking_action:
            raise serializers.ValidationError("Los mensajes de acción requieren booking_action")
        
        return data


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear mensajes"""
    
    class Meta:
        model = Message
        fields = ['message_type', 'content', 'file_id', 'booking_action']
    
    def validate_message_type(self, value):
        """Validar tipo de mensaje"""
        valid_types = ['text', 'image', 'file', 'system', 'booking_action']
        if value not in valid_types:
            raise serializers.ValidationError(f"Tipo de mensaje inválido: {value}")
        return value
    
    def create(self, validated_data):
        """Crear un nuevo mensaje"""
        return Message.objects.create(**validated_data)


class MessageListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de mensajes"""
    
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender_id', 'sender_name', 'message_type', 
            'message_type_display', 'content', 'booking_action',
            'is_read', 'created_at'
        ]


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer completo para conversaciones"""
    
    booking = BookingBasicSerializer(read_only=True)
    participants = ConversationParticipantSerializer(many=True, read_only=True)
    last_message = MessageListSerializer(read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'booking', 'participants', 'last_message',
            'last_message_at', 'created_at'
        ]
        read_only_fields = ['id', 'last_message_at', 'created_at']


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de conversaciones"""
    
    booking_service_title = serializers.CharField(source='booking.service.title', read_only=True)
    booking_status = serializers.CharField(source='booking.status', read_only=True)
    other_user = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message_content = serializers.CharField(source='messages.first.content', read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'booking_service_title', 'booking_status', 
            'other_user', 'unread_count', 'last_message_content',
            'last_message_at', 'created_at'
        ]
    
    def get_other_user(self, obj):
        """Obtener el otro participante"""
        request = self.context.get('request')
        if not request or not hasattr(request, 'jwt_user_id'):
            return None
        
        current_user_id = request.jwt_user_id
        other_participant = obj.participants.exclude(user_id=current_user_id).first()
        
        if other_participant and other_participant.user:
            return UserBasicSerializer(other_participant.user).data
        return None
    
    def get_unread_count(self, obj):
        """Obtener contador de mensajes no leídos para el usuario actual"""
        request = self.context.get('request')
        if not request or not hasattr(request, 'jwt_user_id'):
            return 0
        
        current_user_id = request.jwt_user_id
        participant = obj.participants.filter(user_id=current_user_id).first()
        
        return participant.unread_count if participant else 0


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear conversaciones"""
    
    class Meta:
        model = Conversation
        fields = ['booking']
    
    def validate_booking(self, value):
        """Validar que el booking no tenga ya una conversación"""
        if hasattr(value, 'conversation'):
            raise serializers.ValidationError("Este booking ya tiene una conversación")
        return value
    
    def create(self, validated_data):
        """Crear una nueva conversación con participantes"""
        booking = validated_data['booking']
        conversation = Conversation.objects.create(**validated_data)
        
        # Crear participantes automáticamente
        ConversationParticipant.objects.create(
            conversation=conversation,
            user_id=booking.customer_id
        )
        ConversationParticipant.objects.create(
            conversation=conversation,
            user_id=booking.provider_id
        )
        
        return conversation
