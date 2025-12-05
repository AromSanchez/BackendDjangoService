"""
Serializers para el módulo de chat
"""
from rest_framework import serializers
from .models import Conversation, ConversationParticipant, Message
from apps.bookings.models import Booking
from apps.users.models import User


class UserBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para usuarios en chat"""
    
    avatar_file_id = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'role', 'avatar_file_id']
    
    def get_avatar_file_id(self, obj):
        """Obtener avatar_file_id desde UserProfile"""
        from apps.users.models import UserProfile
        try:
            profile = UserProfile.objects.get(user_id=obj.id)
            return profile.avatar_file_id
        except UserProfile.DoesNotExist:
            return None


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
    conversation_id = serializers.IntegerField(source='conversation.id', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'conversation_id', 'sender_id', 'sender', 'message_type',
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
    booking_service_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'service_id', 'booking', 'booking_service_title', 'participants', 'last_message',
            'last_message_at', 'is_closed', 'created_at'
        ]
        read_only_fields = ['id', 'last_message_at', 'is_closed', 'created_at']

    def get_booking_service_title(self, obj):
        """Obtener título del servicio desde booking o service_id"""
        if obj.booking and obj.booking.service:
            return obj.booking.service.title
        elif obj.service_id:
            # Obtener servicio por service_id
            from apps.services.models import Service
            try:
                service = Service.objects.get(id=obj.service_id)
                return service.title
            except Service.DoesNotExist:
                return None
        return None


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de conversaciones"""
    
    booking_service_title = serializers.SerializerMethodField()
    booking_status = serializers.CharField(source='booking.status', read_only=True)
    booking = BookingBasicSerializer(read_only=True)
    other_user = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    service_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'service_id', 'booking', 'booking_service_title', 'booking_status', 
            'other_user', 'unread_count', 'last_message', 'service_price',
            'last_message_at', 'is_closed', 'created_at'
        ]
    
    def get_booking_service_title(self, obj):
        """Obtener título del servicio desde booking o service_id"""
        if obj.booking and obj.booking.service:
            return obj.booking.service.title
        elif obj.service_id:
            # Obtener servicio por service_id
            from apps.services.models import Service
            try:
                service = Service.objects.get(id=obj.service_id)
                return service.title
            except Service.DoesNotExist:
                return None
        return None
    
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
    
    def get_last_message(self, obj):
        """Obtener último mensaje de la conversación"""
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'content': last_msg.content,
                'created_at': last_msg.created_at,
                'sender_id': last_msg.sender_id
            }
        return None
    
    def get_service_price(self, obj):
        """Obtener precio del servicio"""
        # Primero intentar desde booking
        if obj.booking and obj.booking.service_price:
            return float(obj.booking.service_price)
        if obj.booking and obj.booking.service:
            return float(obj.booking.service.price)
        # Si no hay booking, buscar desde service_id
        if obj.service_id:
            from apps.services.models import Service
            try:
                service = Service.objects.get(id=obj.service_id)
                return float(service.price)
            except Service.DoesNotExist:
                pass
        return 0.0


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
