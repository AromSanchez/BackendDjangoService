"""
Views para el módulo de bookings
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from conectaya.authentication.decorators import jwt_required_drf
from apps.users.models import User
from apps.services.models import Service
from .models import Booking
from .serializers import (
    BookingSerializer, BookingListSerializer, BookingCreateSerializer,
    BookingStatusUpdateSerializer
)
from apps.notifications.services.firebase_service import send_push_notification


def send_booking_message_to_websocket(conversation, message):
    """
    Envía un mensaje de booking a través de WebSocket a todos los participantes
    """
    try:
        from apps.chat.serializers import MessageSerializer
        
        channel_layer = get_channel_layer()
        if not channel_layer:
            print("Channel layer not configured")
            return
        
        # Serializar el mensaje
        message_data = MessageSerializer(message).data
        
        # Obtener participantes de la conversación
        participants = conversation.participants.all()
        
        # Enviar a cada participante
        for participant in participants:
            async_to_sync(channel_layer.group_send)(
                f'user_{participant.user_id}',
                {
                    'type': 'new_message',
                    'message': message_data
                }
            )
        
        print(f"Booking message sent via WebSocket to {len(participants)} participants")
    except Exception as e:
        print(f"Error sending booking message via WebSocket: {e}")


def send_conversation_closed_notification(conversation):
    """
    Envía notificación de cierre de conversación a través de WebSocket
    """
    try:
        from apps.chat.serializers import ConversationSerializer
        
        channel_layer = get_channel_layer()
        if not channel_layer:
            print("Channel layer not configured")
            return
        
        # Serializar la conversación
        conversation_data = ConversationSerializer(conversation).data
        
        # Obtener participantes de la conversación
        participants = conversation.participants.all()
        
        # Enviar a cada participante
        for participant in participants:
            async_to_sync(channel_layer.group_send)(
                f'user_{participant.user_id}',
                {
                    'type': 'conversation_closed',
                    'conversation': conversation_data
                }
            )
        
        print(f"Conversation closed notification sent to {len(participants)} participants")
    except Exception as e:
        print(f"Error sending conversation closed notification: {e}")


@api_view(['GET', 'POST'])
@jwt_required_drf
def bookings_list_create(request):
    """
    GET: Lista bookings del usuario autenticado
    POST: Crea un nuevo booking
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        if request.method == 'GET':
            # Filtrar por rol
            role = request.GET.get('role', 'all')  # all, customer, provider
            
            if role == 'customer':
                bookings = Booking.objects.filter(customer_id=user_id)
            elif role == 'provider':
                bookings = Booking.objects.filter(provider_id=user_id)
            else:
                # Todos los bookings donde participa el usuario
                bookings = Booking.objects.filter(
                    Q(customer_id=user_id) | Q(provider_id=user_id)
                )
            
            # Filtros adicionales
            status_filter = request.GET.get('status')
            if status_filter:
                bookings = bookings.filter(status=status_filter)
            
            bookings = bookings.order_by('-created_at')
            serializer = BookingListSerializer(bookings, many=True)
            
            return Response({
                'bookings': serializer.data,
                'count': bookings.count()
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Solo clientes pueden crear bookings
            if user.role != 'CUSTOMER':
                return Response(
                    {'error': 'Solo los clientes pueden crear solicitudes'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Crear booking
            data = request.data.copy()
            serializer = BookingCreateSerializer(data=data)
            
            if serializer.is_valid():
                service = serializer.validated_data['service']
                booking = serializer.save(
                    customer_id=user_id,
                    provider_id=service.provider_id
                )
                
                # 🔥 Enviar notificación push al proveedor
                send_push_notification(
                    user_id=booking.provider_id,
                    title="Nueva solicitud de servicio 🔔",
                    message=f"{user.first_name} {user.last_name} solicitó tu servicio {service.name}",
                    data={
                        "type": "NEW_BOOKING",
                        "booking_id": str(booking.id),
                        "service_id": str(service.id)
                    }
                )
                
                return Response(
                    BookingSerializer(booking).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT', 'DELETE'])
@jwt_required_drf
def booking_detail(request, booking_id):
    """
    GET: Obtiene detalles de un booking
    PUT: Actualiza un booking
    DELETE: Cancela un booking
    """
    try:
        user_id = request.jwt_user_id
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Verificar permisos (solo participantes pueden ver/modificar)
        if user_id not in [booking.customer_id, booking.provider_id]:
            return Response(
                {'error': 'No tienes permisos para acceder a este booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            serializer = BookingSerializer(booking)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            # Solo permitir actualizar ciertos campos según el rol y estado
            if booking.status in ['completed', 'canceled_by_customer', 'canceled_by_provider', 'rejected']:
                return Response(
                    {'error': 'No se puede modificar un booking finalizado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = BookingSerializer(booking, data=request.data, partial=True)
            if serializer.is_valid():
                booking = serializer.save()
                return Response(
                    BookingSerializer(booking).data,
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # Solo el cliente puede cancelar
            if user_id != booking.customer_id:
                return Response(
                    {'error': 'Solo el cliente puede cancelar la solicitud'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if booking.status not in ['pending', 'negotiating', 'accepted']:
                return Response(
                    {'error': 'No se puede cancelar este booking'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            booking.status = 'canceled_by_customer'
            booking.canceled_at = timezone.now()
            booking.save()
            
            return Response(
                {'message': 'Booking cancelado correctamente'},
                status=status.HTTP_200_OK
            )
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def booking_accept(request, booking_id):
    """
    Aceptar una solicitud de booking (solo proveedor)
    """
    try:
        user_id = request.jwt_user_id
        booking = get_object_or_404(Booking, id=booking_id)
        
        print(f"DEBUG: booking_accept called for booking_id={booking_id}, user_id={user_id}")
        print(f"DEBUG: booking.provider_id={booking.provider_id}, booking.status={booking.status}")

        # Solo el proveedor puede aceptar
        if user_id != booking.provider_id:
            print("DEBUG: Permission denied - user is not provider")
            return Response(
                {'error': 'Solo el proveedor puede aceptar la solicitud'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'pending':
            print(f"DEBUG: Invalid status - {booking.status}")
            return Response(
                {'error': 'Solo se pueden aceptar solicitudes pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'accepted'
        booking.accepted_at = timezone.now()
        booking.save()
        
        # Enviar mensaje al chat
        try:
            from apps.chat.models import Conversation, Message
            conversation = Conversation.objects.filter(booking=booking).first()
            if conversation:
                message = Message.objects.create(
                    conversation=conversation,
                    sender_id=user_id,
                    message_type='booking_action',
                    booking_action='accepted',
                    content='Solicitud aceptada. El servicio ha sido programado.'
                )
                conversation.last_message_at = timezone.now()
                conversation.save()
                
                # Enviar por WebSocket en tiempo real
                send_booking_message_to_websocket(conversation, message)
        except Exception as e:
            print(f"Error sending chat message: {e}")
        
        # 🔥 Enviar notificación push al cliente
        try:
            provider = User.objects.get(id=user_id)
            send_push_notification(
                user_id=booking.customer_id,
                title="Reserva confirmada ✅",
                message=f"{provider.first_name} {provider.last_name} aceptó tu solicitud de {booking.service.name}",
                data={
                    "type": "BOOKING_ACCEPTED",
                    "booking_id": str(booking.id)
                }
            )
        except Exception as e:
            print(f"Error sending push notification: {e}")
        
        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def booking_reject(request, booking_id):
    """
    Rechazar una solicitud de booking (solo proveedor)
    """
    try:
        user_id = request.jwt_user_id
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Solo el proveedor puede rechazar
        if user_id != booking.provider_id:
            return Response(
                {'error': 'Solo el proveedor puede rechazar la solicitud'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'pending':
            return Response(
                {'error': 'Solo se pueden rechazar solicitudes pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'rejected_by_provider'
        booking.cancellation_reason = request.data.get('reason', '')
        booking.canceled_at = timezone.now()
        booking.save()
        
        # Enviar mensaje al chat y cerrar conversación
        try:
            from apps.chat.models import Conversation, Message
            conversation = Conversation.objects.filter(booking=booking).first()
            if conversation:
                reason_text = f" Razón: {booking.cancellation_reason}" if booking.cancellation_reason else ""
                message = Message.objects.create(
                    conversation=conversation,
                    sender_id=user_id,
                    message_type='booking_action',
                    booking_action='rejected',
                    content=f'Solicitud rechazada.{reason_text}'
                )
                conversation.last_message_at = timezone.now()
                conversation.is_closed = True  # Cerrar conversación
                conversation.save()
                
                # Enviar por WebSocket en tiempo real
                send_booking_message_to_websocket(conversation, message)
                
                # Notificar cierre de conversación
                send_conversation_closed_notification(conversation)
        except Exception as e:
            print(f"Error sending chat message: {e}")
        
        # 🔥 Enviar notificación push al cliente
        try:
            provider = User.objects.get(id=user_id)
            send_push_notification(
                user_id=booking.customer_id,
                title="Reserva rechazada ❌",
                message=f"{provider.first_name} {provider.last_name} rechazó tu solicitud de {booking.service.name}",
                data={
                    "type": "BOOKING_REJECTED",
                    "booking_id": str(booking.id)
                }
            )
        except Exception as e:
            print(f"Error sending push notification: {e}")
        
        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def booking_start(request, booking_id):
    """
    Marcar booking como en progreso (solo proveedor)
    """
    try:
        user_id = request.jwt_user_id
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Solo el proveedor puede iniciar
        if user_id != booking.provider_id:
            return Response(
                {'error': 'Solo el proveedor puede iniciar el servicio'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'accepted':
            return Response(
                {'error': 'Solo se pueden iniciar servicios aceptados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'in_progress'
        booking.in_progress_at = timezone.now()
        booking.save()
        
        # Enviar mensaje al chat
        try:
            from apps.chat.models import Conversation, Message
            conversation = Conversation.objects.filter(booking=booking).first()
            if conversation:
                message = Message.objects.create(
                    conversation=conversation,
                    sender_id=user_id,
                    message_type='booking_action',
                    booking_action='in_progress',
                    content='Servicio iniciado. El proveedor ha comenzado el trabajo.'
                )
                conversation.last_message_at = timezone.now()
                conversation.save()
                
                # Enviar por WebSocket en tiempo real
                send_booking_message_to_websocket(conversation, message)
        except Exception as e:
            print(f"Error sending chat message: {e}")
        
        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def booking_complete(request, booking_id):
    """
    Marcar booking como completado (solo proveedor)
    """
    try:
        user_id = request.jwt_user_id
        booking = get_object_or_404(Booking, id=booking_id)
        
        print(f"DEBUG: booking_complete called for booking_id={booking_id}, user_id={user_id}")
        print(f"DEBUG: booking.provider_id={booking.provider_id}, booking.status={booking.status}")

        # Solo el proveedor puede completar
        if user_id != booking.provider_id:
            print("DEBUG: Permission denied - user is not provider")
            return Response(
                {'error': 'Solo el proveedor puede completar el servicio'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status not in ['accepted', 'in_progress']:
            print(f"DEBUG: Invalid status - {booking.status}")
            return Response(
                {'error': 'Solo se pueden completar servicios aceptados o en progreso'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'completed'
        booking.completed_at = timezone.now()
        booking.save()
        
        # Enviar mensaje al chat y cerrar conversación
        try:
            from apps.chat.models import Conversation, Message
            conversation = Conversation.objects.filter(booking=booking).first()
            if conversation:
                message = Message.objects.create(
                    conversation=conversation,
                    sender_id=user_id,
                    message_type='booking_action',
                    booking_action='completed',
                    content='Servicio completado. ¡Gracias por confiar en nosotros!'
                )
                conversation.last_message_at = timezone.now()
                conversation.is_closed = True  # Cerrar conversación
                conversation.save()
                
                # Enviar por WebSocket en tiempo real
                send_booking_message_to_websocket(conversation, message)
                
                # Notificar cierre de conversación
                send_conversation_closed_notification(conversation)
        except Exception as e:
            print(f"Error sending chat message: {e}")
        
        # 🔥 Enviar notificación push al cliente
        try:
            provider = User.objects.get(id=user_id)
            send_push_notification(
                user_id=booking.customer_id,
                title="Servicio completado 🎉",
                message=f"{provider.first_name} {provider.last_name} marcó el servicio como completado",
                data={
                    "type": "BOOKING_COMPLETED",
                    "booking_id": str(booking.id)
                }
            )
        except Exception as e:
            print(f"Error sending push notification: {e}")
        
        # Incrementar ganancias del proveedor
        from apps.users.models import UserProfile
        try:
            provider_profile = UserProfile.objects.get(user_id=user_id)
            # Usar el precio guardado en el booking o el precio actual del servicio
            price = booking.service_price or booking.service.price
            if price:
                provider_profile.add_earnings(price)
        except UserProfile.DoesNotExist:
            # Crear perfil si no existe
            provider_profile = UserProfile.objects.create(user_id=user_id)
            price = booking.service_price or booking.service.price
            if price:
                provider_profile.add_earnings(price)
        
        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@jwt_required_drf
def booking_cancel(request, booking_id):
    """
    Cancelar un booking (solo cliente, solo si está accepted o in_progress)
    """
    try:
        user_id = request.jwt_user_id
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Solo el cliente puede cancelar
        if user_id != booking.customer_id:
            return Response(
                {'error': 'Solo el cliente puede cancelar el servicio'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Solo se puede cancelar si está pending, accepted o in_progress
        if booking.status not in ['pending', 'accepted', 'in_progress']:
            return Response(
                {'error': 'No se puede cancelar este servicio en su estado actual'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener razón (obligatoria)
        cancellation_reason = request.data.get('reason', '').strip()
        if not cancellation_reason:
            return Response(
                {'error': 'La razón de cancelación es obligatoria'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'canceled'
        booking.cancellation_reason = cancellation_reason
        booking.canceled_at = timezone.now()
        booking.save()
        
        # Enviar mensaje al chat y cerrar conversación
        try:
            from apps.chat.models import Conversation, Message
            conversation = Conversation.objects.filter(booking=booking).first()
            if conversation:
                message = Message.objects.create(
                    conversation=conversation,
                    sender_id=user_id,
                    message_type='booking_action',
                    booking_action='canceled',
                    content=f'Servicio cancelado por el cliente. Razón: {cancellation_reason}'
                )
                conversation.last_message_at = timezone.now()
                conversation.is_closed = True  # Cerrar conversación
                conversation.save()
                
                # Enviar por WebSocket en tiempo real
                send_booking_message_to_websocket(conversation, message)
                
                # Notificar cierre de conversación
                send_conversation_closed_notification(conversation)
        except Exception as e:
            print(f"Error sending chat message: {e}")
        
        # 🔥 Enviar notificación push al proveedor
        try:
            client = User.objects.get(id=user_id)
            send_push_notification(
                user_id=booking.provider_id,
                title="Reserva cancelada ⚠️",
                message=f"{client.first_name} {client.last_name} canceló la reserva de {booking.service.name}",
                data={
                    "type": "BOOKING_CANCELLED",
                    "booking_id": str(booking.id)
                }
            )
        except Exception as e:
            print(f"Error sending push notification: {e}")
        
        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@jwt_required_drf
def bookings_stats(request):
    """
    Estadísticas de bookings del usuario
    """
    try:
        user_id = request.jwt_user_id
        user = get_object_or_404(User, id=user_id)
        
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        if user.role == 'CUSTOMER':
            # Estadísticas como cliente
            bookings = Booking.objects.filter(customer_id=user_id)
            
            total_bookings = bookings.count()
            pending_bookings = bookings.filter(status='pending').count()
            completed_bookings = bookings.filter(status='completed').count()
            canceled_bookings = bookings.filter(
                status__in=['canceled_by_customer', 'canceled_by_provider']
            ).count()
            
            # Gastos del mes actual
            current_month = datetime.now().replace(day=1)
            monthly_bookings = bookings.filter(
                created_at__gte=current_month,
                status='completed'
            )
            
            monthly_spent = sum(
                booking.service.price for booking in monthly_bookings
            )
            
            return Response({
                'role': 'customer',
                'total_bookings': total_bookings,
                'pending_bookings': pending_bookings,
                'completed_bookings': completed_bookings,
                'canceled_bookings': canceled_bookings,
                'monthly_spent': monthly_spent,
                'success_rate': (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0
            }, status=status.HTTP_200_OK)
            
        elif user.role == 'PROVIDER':
            # Estadísticas como proveedor
            bookings = Booking.objects.filter(provider_id=user_id)
            
            total_bookings = bookings.count()
            pending_bookings = bookings.filter(status='pending').count()
            completed_bookings = bookings.filter(status='completed').count()
            rejected_bookings = bookings.filter(status='rejected').count()
            
            # Ingresos del mes actual
            current_month = datetime.now().replace(day=1)
            monthly_bookings = bookings.filter(
                created_at__gte=current_month,
                status='completed'
            )
            
            monthly_revenue = sum(
                booking.service.price for booking in monthly_bookings
            )
            
            return Response({
                'role': 'provider',
                'total_bookings': total_bookings,
                'pending_bookings': pending_bookings,
                'completed_bookings': completed_bookings,
                'rejected_bookings': rejected_bookings,
                'monthly_revenue': monthly_revenue,
                'completion_rate': (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0
            }, status=status.HTTP_200_OK)
        
        else:
            return Response(
                {'error': 'Rol no válido para estadísticas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



