import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bk_habitto.settings')
django.setup()

from message.routing import websocket_urlpatterns
from message.middleware import JWTAuthMiddlewareStack, SessionAuthMiddleware

# Usar JWT auth middleware para mejor seguridad
application = ProtocolTypeRouter({
    'websocket': JWTAuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
