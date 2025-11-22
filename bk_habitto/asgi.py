import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bk_habitto.settings')
django.setup()

django_asgi_app = get_asgi_application()

from message.routing import websocket_urlpatterns
from message.middleware import JWTAuthMiddlewareStack, SessionAuthMiddleware

# Usar JWT auth middleware para mejor seguridad
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
