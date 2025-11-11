"""
Cliente para comunicarse con APIs de Spring Boot
"""
import requests
from django.conf import settings


class SpringBootClient:
    """
    Cliente para comunicarse con APIs de Spring Boot
    """
    BASE_URL = getattr(settings, 'SPRINGBOOT_API_URL', 'http://localhost:8080/api')
    INTERNAL_SECRET = getattr(settings, 'INTERNAL_API_SECRET', 'change-this-secret-key')
    
    @staticmethod
    def _get_headers():
        return {
            'X-Internal-Secret': SpringBootClient.INTERNAL_SECRET,
            'Content-Type': 'application/json'
        }
    
    @staticmethod
    def update_reputation(user_id, action, rating=None):
        """
        Actualizar reputación de usuario
        
        Actions disponibles:
        - service_completed
        - service_canceled
        - booking_completed
        - booking_canceled
        - review_received
        - report_received
        """
        try:
            response = requests.post(
                f'{SpringBootClient.BASE_URL}/internal/reputation/update',
                json={
                    'userId': user_id,
                    'action': action,
                    'rating': rating
                },
                headers=SpringBootClient._get_headers(),
                timeout=5
            )
            return response.json() if response.ok else None
        except Exception as e:
            print(f"Error updating reputation: {e}")
            return None
    
    @staticmethod
    def create_notification(user_id, notification_type, title, message, link_url=None, related_id=None):
        """
        Crear notificación en Spring Boot
        """
        try:
            response = requests.post(
                f'{SpringBootClient.BASE_URL}/internal/notifications/create',
                json={
                    'userId': user_id,
                    'type': notification_type,
                    'title': title,
                    'message': message,
                    'linkUrl': link_url,
                    'relatedId': related_id
                },
                headers=SpringBootClient._get_headers(),
                timeout=5
            )
            return response.json() if response.ok else None
        except Exception as e:
            print(f"Error creating notification: {e}")
            return None
    
    @staticmethod
    def get_setting(key):
        """
        Obtener configuración del sistema
        """
        try:
            response = requests.get(
                f'{SpringBootClient.BASE_URL}/internal/settings/{key}',
                headers=SpringBootClient._get_headers(),
                timeout=5
            )
            return response.json() if response.ok else None
        except Exception as e:
            print(f"Error getting setting: {e}")
            return None
    
    @staticmethod
    def get_reputation(user_id):
        """
        Obtener reputación de un usuario
        """
        try:
            response = requests.get(
                f'{SpringBootClient.BASE_URL}/reputation/{user_id}',
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            return response.json() if response.ok else None
        except Exception as e:
            print(f"Error getting reputation: {e}")
            return None
