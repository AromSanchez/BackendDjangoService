"""
Middleware para autenticar requests usando JWT tokens de Spring Boot
"""
from django.contrib.auth.models import User
from django.utils.deprecation import MiddlewareMixin
from .jwt_utils import JWTUtils


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware que intercepta todas las requests y valida el JWT token
    del header Authorization
    """
    
    def process_request(self, request):
        """
        Procesa cada request para extraer y validar el JWT token
        """
        # Obtener el header Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            # Extraer el token (remover "Bearer ")
            token = auth_header[7:]
            
            # Decodificar el token para obtener el ID del usuario
            user_id = JWTUtils.get_user_id_from_token(token)
            
            if user_id:
                try:
                    # Buscar el usuario en la base de datos por ID
                    user = User.objects.filter(id=user_id).first()
                    
                    if user:
                        # Adjuntar el usuario autenticado al request
                        request.user = user
                        request.jwt_user_id = user_id
                        request.jwt_token = token
                    else:
                        # Usuario no existe en Django, pero el token es válido
                        # Guardar el ID para uso posterior
                        request.jwt_user_id = user_id
                        request.jwt_token = token
                        
                except Exception as e:
                    print(f"Error al buscar usuario: {e}")
        
        return None
