"""
WebSocket consumers para el sistema de chat
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from conectaya.authentication.jwt_utils import JWTUtils
from apps.users.models import User
from apps.chat.models import Conversation, Message
from apps.chat.serializers import MessageSerializer

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer para manejar conexiones WebSocket del chat
    """
    
    async def connect(self):
        """
        Manejar nueva conexión WebSocket
        """
        # Obtener usuario autenticado del scope (ya autenticado por middleware)
        self.user = self.scope.get('user', AnonymousUser())

        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            logger.warning("Conexión WebSocket rechazada: usuario no autenticado")
            await self.close()
            return
        
        # Agregar usuario al grupo personal
        self.user_group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        # Aceptar conexión
        await self.accept()
        
        logger.info(f"Usuario {self.user.id} conectado al WebSocket")
        
        # Enviar confirmación de conexión
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado al chat en tiempo real'
        }))

    async def disconnect(self, close_code):
        """
        Manejar desconexión WebSocket
        """
        if hasattr(self, 'user') and self.user and self.user != AnonymousUser():
            # Remover del grupo personal
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            logger.info(f"Usuario {self.user.id} desconectado del WebSocket")

    async def receive(self, text_data):
        """
        Manejar mensajes recibidos del WebSocket
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data.get('data', {}))
            elif message_type == 'typing':
                await self.handle_typing(data.get('data', {}))
            else:
                logger.warning(f"Tipo de mensaje desconocido: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Error decodificando mensaje JSON")
            await self.send_error("Formato de mensaje inválido")
        except Exception as e:
            logger.error(f"Error procesando mensaje WebSocket: {e}")
            await self.send_error("Error procesando mensaje")

    async def handle_chat_message(self, data):
        """
        Manejar envío de mensaje de chat
        """
        chat_id = data.get('chat_id')
        content = data.get('content')
        
        if not chat_id or not content:
            await self.send_error("chat_id y content son requeridos")
            return
        
        try:
            # Verificar que la conversación existe y el usuario tiene acceso
            conversation = await self.get_conversation(chat_id)
            if not conversation:
                await self.send_error("Conversación no encontrada")
                return
            
            # Crear el mensaje
            message = await self.create_message(conversation, content)
            
            # Serializar mensaje
            message_data = await self.serialize_message(message)
            
            # Enviar mensaje a ambos participantes
            participants = await self.get_conversation_participants(conversation)
            
            for participant in participants:
                await self.channel_layer.group_send(
                    f'user_{participant.id}',
                    {
                        'type': 'new_message',
                        'message': message_data
                    }
                )
                
            logger.info(f"Mensaje enviado en conversación {chat_id}")
            
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            await self.send_error("Error enviando mensaje")

    async def handle_typing(self, data):
        """
        Manejar indicador de escritura
        """
        chat_id = data.get('chat_id')
        is_typing = data.get('is_typing', True)
        
        if not chat_id:
            return
        
        try:
            # Obtener conversación
            conversation = await self.get_conversation(chat_id)
            if not conversation:
                return
            
            # Obtener el otro participante
            other_participant = await self.get_other_participant(conversation)
            if other_participant:
                await self.channel_layer.group_send(
                    f'user_{other_participant.id}',
                    {
                        'type': 'typing_indicator',
                        'chat_id': chat_id,
                        'user_id': self.user.id,
                        'is_typing': is_typing
                    }
                )
                
        except Exception as e:
            logger.error(f"Error manejando typing: {e}")

    async def new_message(self, event):
        """
        Enviar nuevo mensaje al WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'data': event['message']
        }))

    async def typing_indicator(self, event):
        """
        Enviar indicador de escritura al WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'data': {
                'chat_id': event['chat_id'],
                'user_id': event['user_id'],
                'is_typing': event['is_typing']
            }
        }))

    async def send_error(self, message):
        """
        Enviar mensaje de error al WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    # Métodos de base de datos (síncronos convertidos a asíncronos)
    
    @database_sync_to_async
    def authenticate_user(self, token):
        """
        Autenticar usuario usando JWT token
        """
        if not token:
            return AnonymousUser()
        
        try:
            user_id = JWTUtils.get_user_id_from_token(token)
            if user_id:
                return User.objects.get(id=user_id)
        except (User.DoesNotExist, Exception) as e:
            logger.error(f"Error autenticando usuario: {e}")
        
        return AnonymousUser()

    @database_sync_to_async
    def get_conversation(self, conversation_id):
        """
        Obtener conversación por ID
        """
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            # Verificar que el usuario tiene acceso a esta conversación
            if (conversation.user1_id == self.user.id or 
                conversation.user2_id == self.user.id):
                return conversation
        except Conversation.DoesNotExist:
            pass
        return None

    @database_sync_to_async
    def create_message(self, conversation, content):
        """
        Crear nuevo mensaje
        """
        return Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )

    @database_sync_to_async
    def serialize_message(self, message):
        """
        Serializar mensaje para envío
        """
        serializer = MessageSerializer(message)
        return serializer.data

    @database_sync_to_async
    def get_conversation_participants(self, conversation):
        """
        Obtener participantes de la conversación
        """
        return [conversation.user1, conversation.user2]

    @database_sync_to_async
    def get_other_participant(self, conversation):
        """
        Obtener el otro participante de la conversación
        """
        if conversation.user1_id == self.user.id:
            return conversation.user2
        else:
            return conversation.user1
