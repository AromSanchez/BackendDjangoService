"""
Utilidad para decodificar y validar JWT tokens generados por Spring Boot
"""
import jwt
from datetime import datetime
from django.conf import settings


class JWTUtils:
    """
    Clase para manejar la decodificación y validación de JWT tokens
    que vienen del backend de Spring Boot
    """
    
    @staticmethod
    def decode_access_token(token):
        """
        Decodifica y valida un access token de Spring Boot
        
        Args:
            token (str): El token JWT a decodificar
            
        Returns:
            dict: Los claims del token si es válido
            None: Si el token es inválido o ha expirado
        """
        try:
            # Decodificar el token usando la misma secret key que Spring Boot
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256']
            )
            
            # Verificar que no esté expirado (jwt.decode ya lo hace automáticamente)
            # pero podemos hacer validaciones adicionales si es necesario
            
            return payload
            
        except jwt.ExpiredSignatureError:
            print("Token expirado")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Token inválido: {e}")
            return None
    
    @staticmethod
    def decode_refresh_token(token):
        """
        Decodifica y valida un refresh token de Spring Boot
        
        Args:
            token (str): El refresh token JWT a decodificar
            
        Returns:
            dict: Los claims del token si es válido
            None: Si el token es inválido o ha expirado
        """
        try:
            # Decodificar usando la secret key del refresh token
            payload = jwt.decode(
                token,
                settings.JWT_REFRESH_SECRET_KEY,
                algorithms=['HS256']
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            print("Refresh token expirado")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Refresh token inválido: {e}")
            return None
    
    @staticmethod
    def get_user_id_from_token(token):
        """
        Extrae el ID del usuario (subject) del access token
        
        Args:
            token (str): El token JWT
            
        Returns:
            int: El ID del usuario
            None: Si el token es inválido
        """
        payload = JWTUtils.decode_access_token(token)
        if payload:
            user_id_str = payload.get('sub')  # 'sub' es donde Spring Boot guarda el ID
            try:
                return int(user_id_str)
            except (ValueError, TypeError):
                return None
        return None
