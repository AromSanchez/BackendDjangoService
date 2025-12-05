import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging
import os
import json

logger = logging.getLogger(__name__)

# Inicializar Firebase Admin SDK (solo una vez)
if not firebase_admin._apps:
    # Opción 1: Usar variable de entorno (para Render)
    firebase_credentials_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
    
    if firebase_credentials_json:
        # Cargar credenciales desde variable de entorno
        cred_dict = json.loads(firebase_credentials_json)
        cred = credentials.Certificate(cred_dict)
        logger.info("🔥 Firebase inicializado desde variable de entorno")
    else:
        # Opción 2: Usar archivo local (para desarrollo)
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        logger.info("🔥 Firebase inicializado desde archivo local")
    
    firebase_admin.initialize_app(cred)


def send_push_notification(user_id: int, title: str, message: str, data: dict = None):
    """
    Envía una notificación push a un usuario específico
    
    Args:
        user_id: ID del usuario destinatario
        title: Título de la notificación
        message: Mensaje de la notificación
        data: Datos adicionales (opcional)
    
    Returns:
        bool: True si se envió exitosamente, False en caso contrario
    """
    from apps.notifications.models import DeviceToken
    
    # Log de entrada para debug
    print(f"📤 Intentando enviar push a user_id={user_id}: {title}")
    logger.info(f"📤 Intentando enviar push a user_id={user_id}: {title}")
    
    try:
        # Obtener todos los tokens del usuario
        tokens = list(DeviceToken.objects.filter(user_id=user_id).values_list('token', flat=True))
        
        if not tokens:
            print(f"⚠️ No se encontraron tokens FCM para user_id={user_id}")
            logger.warning(f"⚠️ No se encontraron tokens para user_id={user_id}")
            return False
        
        print(f"📱 Encontrados {len(tokens)} tokens para user_id={user_id}")
        
        # Construir el mensaje
        notification = messaging.Notification(
            title=title,
            body=message
        )
        
        # Datos adicionales (opcional) - convertir a strings
        message_data = {k: str(v) for k, v in (data or {}).items()}
        
        # Enviar a cada dispositivo individualmente
        # Usamos send() individual en lugar de send_all() que está deprecado
        success_count = 0
        failure_count = 0
        
        for token in tokens:
            try:
                fcm_message = messaging.Message(
                    notification=notification,
                    data=message_data,
                    token=token
                )
                
                # Enviar mensaje individual
                response = messaging.send(fcm_message)
                print(f"✅ Notificación enviada exitosamente: {response}")
                success_count += 1
                
            except messaging.UnregisteredError:
                # Token inválido, eliminarlo
                DeviceToken.objects.filter(token=token).delete()
                print(f"🗑️ Token inválido eliminado: {token[:20]}...")
                logger.warning(f"🗑️ Token inválido eliminado: {token[:20]}...")
                failure_count += 1
                
            except Exception as e:
                print(f"❌ Error enviando a token {token[:20]}...: {str(e)}")
                logger.error(f"❌ Error enviando a token: {str(e)}")
                failure_count += 1
        
        print(f"📊 Resultado: {success_count} enviadas, {failure_count} fallidas para user_id={user_id}")
        logger.info(f"✅ Notificaciones enviadas: {success_count}/{len(tokens)} para user_id={user_id}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error al enviar notificación push: {str(e)}")
        logger.error(f"❌ Error al enviar notificación: {str(e)}")
        return False
