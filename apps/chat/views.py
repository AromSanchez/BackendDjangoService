"""
Views para el módulo de chat
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from conectaya.authentication.decorators import jwt_required_drf
from apps.users.models import User
from apps.bookings.models import Booking
from .models import Conversation, ConversationParticipant, Message
from .serializers import (
    ConversationSerializer, ConversationListSerializer, ConversationCreateSerializer,
    MessageSerializer, MessageListSerializer, MessageCreateSerializer
)


@api_view(['GET', 'POST'])
@jwt_required_drf
def conversations_list_create(request):
    """
    GET: Lista conversaciones del usuario autenticado
    POST: Crea una nueva conversación
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if request.method == 'GET':
            # Lista conversaciones donde participa el usuario y no ha sido eliminada
            conversations = Conversation.objects.filter(
                participants__user_id=user_id,
                participants__deleted_at__isnull=True
            ).order_by('-last_message_at')
            
            serializer = ConversationListSerializer(
                conversations, 
                many=True,
                context={'request': request}
            )
            return Response({
                'conversations': serializer.data,
                'count': conversations.count()
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Crear conversación
            data = request.data.copy()
            serializer = ConversationCreateSerializer(data=data)
            
            if serializer.is_valid():
                booking = serializer.validated_data['booking']
                
                # Verificar que el usuario participe en el booking
                if user_id not in [booking.customer_id, booking.provider_id]:
                    return Response(
                        {'error': 'No tienes permisos para crear esta conversación'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                conversation = serializer.save()
                
                return Response(
                    ConversationSerializer(conversation).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def conversation_detail(request, conversation_id):
    """
    Obtiene detalles de una conversación
    """
    try:
        user_id = request.jwt_user_id
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Verificar que el usuario participe en la conversación
        participant = conversation.participants.filter(user_id=user_id).first()
        if not participant:
            return Response(
                {'error': 'No tienes permisos para acceder a esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
@jwt_required_drf
def conversation_messages(request, conversation_id):
    """
    GET: Lista mensajes de una conversación
    POST: Envía un nuevo mensaje
    """
    try:
        user_id = request.jwt_user_id
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Verificar que el usuario participe en la conversación
        participant = conversation.participants.filter(user_id=user_id).first()
        if not participant:
            return Response(
                {'error': 'No tienes permisos para acceder a esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            # Lista mensajes de la conversación
            messages = conversation.messages.order_by('-created_at')
            
            # Filtrar mensajes anteriores a la fecha de vaciado si existe
            if participant.cleared_at:
                messages = messages.filter(created_at__gt=participant.cleared_at)
            
            # Paginación simple
            limit = int(request.GET.get('limit', 50))
            offset = int(request.GET.get('offset', 0))
            
            messages = messages[offset:offset + limit]
            
            serializer = MessageListSerializer(messages, many=True)
            return Response({
                'messages': serializer.data,
                'count': len(serializer.data)
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Verificar si la conversación está cerrada
            if conversation.is_closed:
                return Response(
                    {'error': 'Esta conversación ha finalizado y no se pueden enviar más mensajes'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Enviar mensaje
            from datetime import timedelta
            data = request.data.copy()
            serializer = MessageCreateSerializer(data=data)
            
            if serializer.is_valid():
                message = serializer.save(
                    conversation=conversation,
                    sender_id=user_id
                )
                
                # Actualizar timestamp de la conversación
                conversation.last_message_at = timezone.now()
                conversation.save()
                
                # Incrementar contador de no leídos para otros participantes y reactivar chat si estaba eliminado
                other_participants = conversation.participants.exclude(user_id=user_id)
                for other_participant in other_participants:
                    other_participant.unread_count += 1
                    # Reactivar chat si estaba eliminado (soft delete)
                    # y limpiar historial para que solo se vean mensajes nuevos
                    if other_participant.deleted_at:
                        other_participant.deleted_at = None
                        # Establecer cleared_at justo antes del mensaje actual para que este mensaje SÍ se vea
                        other_participant.cleared_at = message.created_at - timedelta(seconds=1)
                    other_participant.save()
                
                return Response(
                    MessageSerializer(message).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@jwt_required_drf
def conversation_mark_read(request, conversation_id):
    """
    Marcar conversación como leída
    """
    try:
        user_id = request.jwt_user_id
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Verificar que el usuario participe en la conversación
        participant = conversation.participants.filter(user_id=user_id).first()
        if not participant:
            return Response(
                {'error': 'No tienes permisos para acceder a esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Marcar mensajes como leídos
        unread_messages = conversation.messages.filter(
            is_read=False
        ).exclude(sender_id=user_id)
        
        unread_messages.update(is_read=True)
        
        # Resetear contador de no leídos
        participant.unread_count = 0
        participant.last_read_at = timezone.now()
        participant.save()
        
        return Response({
            'message': 'Conversación marcada como leída',
            'messages_marked': unread_messages.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['POST'])
@jwt_required_drf
def clear_conversation_history(request, conversation_id):
    """
    Vaciar historial de chat para el usuario actual
    """
    try:
        user_id = request.jwt_user_id
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Verificar que el usuario participe en la conversación
        participant = conversation.participants.filter(user_id=user_id).first()
        if not participant:
            return Response(
                {'error': 'No tienes permisos para acceder a esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Actualizar fecha de vaciado
        participant.cleared_at = timezone.now()
        participant.save()
        
        return Response({
            'message': 'Historial de chat vaciado correctamente'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@jwt_required_drf
def delete_conversation(request, conversation_id):
    """
    Eliminar conversación (soft delete para el usuario actual)
    """
    try:
        user_id = request.jwt_user_id
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Verificar que el usuario participe en la conversación
        participant = conversation.participants.filter(user_id=user_id).first()
        if not participant:
            return Response(
                {'error': 'No tienes permisos para acceder a esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Marcar como eliminado (soft delete)
        participant.deleted_at = timezone.now()
        participant.save()
        
        return Response({
            'message': 'Conversación eliminada correctamente'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def conversation_by_booking(request, booking_id):
    """
    Obtiene o crea conversación para un booking específico
    """
    try:
        user_id = request.jwt_user_id
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Verificar que el usuario participe en el booking
        if user_id not in [booking.customer_id, booking.provider_id]:
            return Response(
                {'error': 'No tienes permisos para acceder a esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Buscar conversación existente
        conversation = getattr(booking, 'conversation', None)
        
        if not conversation:
            # Crear conversación automáticamente
            conversation = Conversation.objects.create(booking=booking)
            
            # Crear participantes
            ConversationParticipant.objects.create(
                conversation=conversation,
                user_id=booking.customer_id
            )
            ConversationParticipant.objects.create(
                conversation=conversation,
                user_id=booking.provider_id
            )
        
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def chat_stats(request):
    """
    Estadísticas de chat del usuario
    """
    try:
        user_id = request.jwt_user_id
        
        # Conversaciones del usuario
        conversations = Conversation.objects.filter(
            participants__user_id=user_id
        )
        
        total_conversations = conversations.count()
        
        # Mensajes no leídos
        participant = ConversationParticipant.objects.filter(user_id=user_id)
        total_unread = sum(p.unread_count for p in participant)
        
        # Conversaciones activas (con mensajes recientes)
        from datetime import datetime, timedelta
        week_ago = timezone.now() - timedelta(days=7)
        
        active_conversations = conversations.filter(
            last_message_at__gte=week_ago
        ).count()
        
        return Response({
            'total_conversations': total_conversations,
            'total_unread_messages': total_unread,
            'active_conversations': active_conversations
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def send_booking_action_message(request, conversation_id):
    """
    Enviar mensaje de acción de booking (aceptar, rechazar, etc.)
    """
    try:
        from datetime import timedelta
        user_id = request.jwt_user_id
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Verificar que el usuario participe en la conversación
        participant = conversation.participants.filter(user_id=user_id).first()
        if not participant:
            return Response(
                {'error': 'No tienes permisos para acceder a esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        booking_action = request.data.get('booking_action')
        if not booking_action:
            return Response(
                {'error': 'booking_action es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar acciones válidas
        valid_actions = [
            'request_acceptance', 'accept', 'reject', 'mark_complete', 
            'confirm_complete', 'cancel', 'start_service'
        ]
        
        if booking_action not in valid_actions:
            return Response(
                {'error': 'Acción de booking inválida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear mensaje de acción
        message = Message.objects.create(
            conversation=conversation,
            sender_id=user_id,
            message_type='booking_action',
            booking_action=booking_action,
            content=request.data.get('content', '')
        )
        
        # Actualizar timestamp de la conversación
        conversation.last_message_at = timezone.now()
        conversation.save()
        
        # Incrementar contador de no leídos para otros participantes y reactivar chat
        other_participants = conversation.participants.exclude(user_id=user_id)
        for other_participant in other_participants:
            other_participant.unread_count += 1
            # Reactivar chat si estaba eliminado y limpiar historial
            if other_participant.deleted_at:
                other_participant.deleted_at = None
                other_participant.cleared_at = message.created_at - timedelta(seconds=1)
            other_participant.save()
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def send_file_message(request, conversation_id):
    """
    Enviar mensaje con archivo (imagen o documento)
    """
    try:
        from datetime import timedelta
        user_id = request.jwt_user_id
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Verificar que el usuario participe en la conversación
        participant = conversation.participants.filter(user_id=user_id).first()
        if not participant:
            return Response(
                {'error': 'No tienes permisos para acceder a esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        file_id = request.data.get('file_id')
        message_type = request.data.get('message_type', 'file')  # 'image' o 'file'
        
        if not file_id:
            return Response(
                {'error': 'file_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if message_type not in ['image', 'file']:
            return Response(
                {'error': 'message_type debe ser "image" o "file"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear mensaje con archivo
        message = Message.objects.create(
            conversation=conversation,
            sender_id=user_id,
            message_type=message_type,
            file_id=file_id,
            content=request.data.get('content', '')
        )
        
        # Actualizar timestamp de la conversación
        conversation.last_message_at = timezone.now()
        conversation.save()
        
        # Incrementar contador de no leídos para otros participantes y reactivar chat
        other_participants = conversation.participants.exclude(user_id=user_id)
        for other_participant in other_participants:
            other_participant.unread_count += 1
            # Reactivar chat si estaba eliminado y limpiar historial
            if other_participant.deleted_at:
                other_participant.deleted_at = None
                other_participant.cleared_at = message.created_at - timedelta(seconds=1)
            other_participant.save()
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def conversation_search_messages(request, conversation_id):
    """
    Buscar mensajes en una conversación
    """
    try:
        user_id = request.jwt_user_id
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Verificar que el usuario participe en la conversación
        participant = conversation.participants.filter(user_id=user_id).first()
        if not participant:
            return Response(
                {'error': 'No tienes permisos para acceder a esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        search_query = request.GET.get('q', '').strip()
        if not search_query:
            return Response(
                {'error': 'Parámetro de búsqueda "q" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar mensajes que contengan el texto
        messages = conversation.messages.filter(
            content__icontains=search_query,
            message_type='text'
        ).order_by('-created_at')[:20]
        
        serializer = MessageListSerializer(messages, many=True)
        return Response({
            'messages': serializer.data,
            'count': len(serializer.data),
            'search_query': search_query
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def conversations_unread_count(request):
    """
    Obtener contador total de mensajes no leídos
    """
    try:
        user_id = request.jwt_user_id
        
        # Sumar todos los contadores de no leídos
        participants = ConversationParticipant.objects.filter(user_id=user_id)
        total_unread = sum(p.unread_count for p in participants)
        
        return Response({
            'total_unread_messages': total_unread
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def create_booking_from_chat(request, conversation_id):
    """
    Crear un booking desde una conversación de chat
    """
    try:
        from datetime import timedelta
        user_id = request.jwt_user_id
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Verificar que el usuario participe en la conversación
        participant = conversation.participants.filter(user_id=user_id).first()
        if not participant:
            return Response(
                {'error': 'No tienes permisos para acceder a esta conversación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar que el usuario sea cliente
        user = get_object_or_404(User, id=user_id)
        if user.role != 'CUSTOMER':
            return Response(
                {'error': 'Solo los clientes pueden crear solicitudes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener datos del booking
        from apps.services.models import Service
        service_id = request.data.get('service_id')
        if not service_id:
            return Response(
                {'error': 'service_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = get_object_or_404(Service, id=service_id)
        
        # Crear el booking
        booking = Booking.objects.create(
            service=service,
            customer_id=user_id,
            provider_id=service.provider_id,
            service_price=service.price,
            booking_notes=request.data.get('notes', ''),
            booking_date=request.data.get('booking_date'),
            booking_time=request.data.get('booking_time'),
            customer_address=request.data.get('customer_address'),
            status='pending'
        )
        
        # Crear mensaje de sistema en el chat
        message = Message.objects.create(
            conversation=conversation,
            sender_id=user_id,
            message_type='booking_action',
            booking_action='request_acceptance',
            content=f'Solicitud de servicio enviada: {service.title} - S/{service.price}'
        )
        
        # Actualizar timestamp de la conversación y vincular booking
        conversation.last_message_at = timezone.now()
        conversation.booking = booking
        conversation.save()
        
        # Incrementar contador de no leídos para el proveedor y reactivar chat
        other_participants = conversation.participants.exclude(user_id=user_id)
        for other_participant in other_participants:
            other_participant.unread_count += 1
            # Reactivar chat si estaba eliminado y limpiar historial
            if other_participant.deleted_at:
                other_participant.deleted_at = None
                other_participant.cleared_at = message.created_at - timedelta(seconds=1)
            other_participant.save()
        
        # Enviar por WebSocket en tiempo real
        from apps.bookings.views import send_booking_message_to_websocket
        send_booking_message_to_websocket(conversation, message)
        
        # 🔥 Enviar notificación push al proveedor
        try:
            from apps.notifications.services.firebase_service import send_push_notification
            send_push_notification(
                user_id=booking.provider_id,
                title="Nueva solicitud de servicio 🔔",
                message=f"{user.first_name} {user.last_name} solicitó tu servicio {service.title}",
                data={
                    "type": "NEW_BOOKING",
                    "booking_id": str(booking.id),
                    "service_id": str(service.id)
                }
            )
        except Exception as e:
            print(f"Error sending push notification: {e}")
        
        from apps.bookings.serializers import BookingSerializer
        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def create_or_get_conversation_by_service(request, service_id):
    """
    Obtener o crear conversación para un servicio específico
    La conversación se crea SIN booking. El booking se crea después cuando el cliente solicita.
    """
    try:
        user_id = request.jwt_user_id
        from apps.services.models import Service
        service = get_object_or_404(Service, id=service_id)
        
        # Verificar que el usuario no sea el proveedor del servicio
        if user_id == service.provider_id:
            return Response(
                {'error': 'No puedes iniciar un chat con tu propio servicio'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar conversación existente para este servicio entre cliente y proveedor
        existing_conversation = Conversation.objects.filter(
            service_id=service_id,
            participants__user_id=user_id
        ).filter(
            participants__user_id=service.provider_id
        ).first()
        
        if existing_conversation:
            # Ya existe una conversación
            conversation = existing_conversation
            
            # Reactivar conversación para AMBOS participantes si alguno la había eliminado
            participants = conversation.participants.filter(deleted_at__isnull=False)
            for participant in participants:
                participant.deleted_at = None
                participant.save()
        else:
            # Crear nueva conversación SIN booking
            conversation = Conversation.objects.create(
                service_id=service_id
            )
            
            # Crear participantes
            ConversationParticipant.objects.create(
                conversation=conversation,
                user_id=user_id
            )
            ConversationParticipant.objects.create(
                conversation=conversation,
                user_id=service.provider_id
            )
            
            # Mensaje de bienvenida
            Message.objects.create(
                conversation=conversation,
                sender_id=user_id,
                message_type='system',
                content=f'Conversación iniciada sobre el servicio: {service.title}'
            )
            
            conversation.last_message_at = timezone.now()
            conversation.save()
        
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def get_provider_earnings(request):
    """
    Obtener estadísticas de ganancias del proveedor
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        # Verificar que sea proveedor
        if user.role != 'PROVIDER':
            return Response(
                {'error': 'Solo los proveedores pueden ver sus ganancias'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from apps.users.models import UserProfile
        from datetime import datetime, timedelta
        
        # Obtener o crear perfil
        profile, created = UserProfile.objects.get_or_create(user_id=user_id)
        
        # Ganancias totales
        total_earnings = profile.total_earnings
        
        # Bookings completados
        completed_bookings = Booking.objects.filter(
            provider_id=user_id,
            status='completed'
        ).order_by('-completed_at')
        
        # Ganancias del mes actual
        current_month = datetime.now().replace(day=1)
        monthly_bookings = completed_bookings.filter(
            completed_at__gte=current_month
        )
        
        monthly_earnings = sum(
            (booking.service_price or booking.service.price or 0) 
            for booking in monthly_bookings
        )
        
        # Últimos servicios completados
        recent_completed = []
        for booking in completed_bookings[:10]:
            recent_completed.append({
                'id': booking.id,
                'service_title': booking.service.title,
                'price': float(booking.service_price or booking.service.price or 0),
                'completed_at': booking.completed_at,
                'customer_name': booking.customer.full_name if booking.customer else 'N/A'
            })
        
        return Response({
            'total_earnings': float(total_earnings),
            'monthly_earnings': float(monthly_earnings),
            'total_completed_services': completed_bookings.count(),
            'monthly_completed_services': monthly_bookings.count(),
            'recent_completed': recent_completed
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

