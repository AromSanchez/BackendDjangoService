"""
Backend de autenticación personalizado para JWT tokens de Spring Boot
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .jwt_utils import JWTUtils


class JWTAuthenticationBackend(BaseBackend):
    """
    Backend de autenticación que valida JWT tokens de Spring Boot
    """
    
    def authenticate(self, request, token=None, **kwargs):
        """
        Autentica un usuario usando un JWT token
        
        Args:
            request: El request HTTP
            token: El JWT token a validar
            
        Returns:
            User: El usuario autenticado si el token es válido
            None: Si el token es inválido
        """
        if token is None:
            return None
        
        # Decodificar el token para obtener el ID
        user_id = JWTUtils.get_user_id_from_token(token)
        
        if user_id:
            try:
                # Buscar el usuario por ID
                user = User.objects.filter(id=user_id).first()
                
                if user:
                    return user
                else:
                    print(f"Usuario con ID {user_id} no encontrado en Django")
                    return None
                
            except Exception as e:
                print(f"Error en autenticación JWT: {e}")
                return None
        
        return None
    
    def get_user(self, user_id):
        """
        Obtiene un usuario por su ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
