from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs
import jwt
from django.conf import settings

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_string):
    """
    Obtener usuario desde token JWT
    """
    try:
        # Decodificar el token
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
        return user
    except Exception:
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware personalizado para autenticación JWT en WebSockets
    """
    
    async def __call__(self, scope, receive, send):
        # Obtener token de los parámetros de la query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        # Buscar token en query params (token=xxx) o en headers
        token = None
        if 'token' in query_params:
            token = query_params['token'][0]
        else:
            # Buscar en headers
            headers = dict(scope.get('headers', []))
            if b'authorization' in headers:
                auth_header = headers[b'authorization'].decode()
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]  # Remover 'Bearer ' prefix
        
        # Autenticar usuario si hay token
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
            
        return await super().__call__(scope, receive, send)

def JWTAuthMiddlewareStack(inner):
    """
    Función helper para aplicar el middleware de autenticación JWT
    """
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))

# Middleware alternativo más simple que usa la sesión de Django
class SessionAuthMiddleware(BaseMiddleware):
    """
    Middleware para autenticación basada en sesión (más simple para desarrollo)
    """
    
    async def __call__(self, scope, receive, send):
        # Obtener usuario de la sesión si existe
        from channels.auth import get_user
        
        # Intentar obtener usuario de la sesión
        user = await get_user(scope)
        scope['user'] = user
        
        return await super().__call__(scope, receive, send)