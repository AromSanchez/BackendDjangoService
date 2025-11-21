"""
ASGI config for conectaya project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conectaya.settings')

# Inicializar Django ASGI application temprano para asegurar que el AppRegistry
# esté poblado antes de importar código que pueda importar modelos ORM.
django.setup()
django_asgi_app = get_asgi_application()

# Importar después de django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from conectaya.routing import websocket_urlpatterns
from conectaya.authentication.websocket_middleware import JWTAuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
