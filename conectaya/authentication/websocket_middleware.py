"""
Middleware de autenticación JWT para WebSockets
"""
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from .jwt_utils import JWTUtils
from apps.users.models import User


@database_sync_to_async
def get_user_from_token(token):
    """
    Obtener usuario desde token JWT
    """
    try:
        user_id = JWTUtils.get_user_id_from_token(token)
        if user_id:
            return User.objects.get(id=user_id)
    except (User.DoesNotExist, Exception):
        pass
    return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware personalizado para autenticar WebSockets con JWT
    """
    
    async def __call__(self, scope, receive, send):
        # Obtener token de query parameters
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        # Autenticar usuario
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    Stack de middleware que incluye autenticación JWT
    """
    return JWTAuthMiddleware(inner)
