import json
import logging
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import time

# Configurar logger específico para API
logger = logging.getLogger('api_logger')

class APILoggingMiddleware(MiddlewareMixin):
    """
    Middleware para logging de requests y responses de la API.
    Solo se activa cuando DEBUG=True en settings.
    """
    
    def process_request(self, request):
        """
        Procesa el request entrante y lo registra si DEBUG está habilitado
        """
        if not settings.DEBUG:
            return None
            
        # Solo loggear endpoints de API
        if not request.path.startswith('/api/'):
            return None
            
        # Guardar tiempo de inicio para medir duración
        request._start_time = time.time()
        
        # Preparar datos del request
        request_data = {
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
            'ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # Agregar body para POST, PUT, PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.content_type == 'application/json':
                    body = json.loads(request.body.decode('utf-8'))
                    # Ocultar campos sensibles
                    body = self.sanitize_sensitive_data(body)
                    request_data['body'] = body
                elif request.content_type.startswith('multipart/form-data'):
                    # Para archivos, solo mostrar los nombres de campos
                    request_data['body'] = {
                        'form_fields': list(request.POST.keys()),
                        'files': list(request.FILES.keys())
                    }
                else:
                    request_data['body'] = 'Non-JSON content'
            except (json.JSONDecodeError, UnicodeDecodeError):
                request_data['body'] = 'Invalid or binary content'
        
        # Log del request
        logger.info(f"📥 REQUEST: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
        
        return None
    
    def process_response(self, request, response):
        """
        Procesa la response y la registra si DEBUG está habilitado
        """
        if not settings.DEBUG:
            return response
            
        # Solo loggear endpoints de API
        if not request.path.startswith('/api/'):
            return response
            
        # Calcular duración de la request
        duration = None
        if hasattr(request, '_start_time'):
            duration = round((time.time() - request._start_time) * 1000, 2)  # en milisegundos
        
        # Preparar datos de la response
        response_data = {
            'status_code': response.status_code,
            'duration_ms': duration,
            'content_type': response.get('Content-Type', ''),
        }
        
        # Agregar contenido de la response si es JSON
        try:
            if response.get('Content-Type', '').startswith('application/json'):
                content = json.loads(response.content.decode('utf-8'))
                # Limitar el tamaño del contenido loggeado
                if len(str(content)) > 5000:  # Si es muy largo, truncar
                    response_data['content'] = 'Response too large to log (>5000 chars)'
                    response_data['content_size'] = len(str(content))
                else:
                    response_data['content'] = content
            else:
                response_data['content'] = f'Non-JSON response ({len(response.content)} bytes)'
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            response_data['content'] = 'Invalid or binary response'
        
        # Determinar el nivel de log basado en el status code
        if response.status_code >= 500:
            log_level = 'error'
            emoji = '❌'
        elif response.status_code >= 400:
            log_level = 'warning'
            emoji = '⚠️'
        else:
            log_level = 'info'
            emoji = '📤'
        
        # Log de la response
        log_message = f"{emoji} RESPONSE [{request.method} {request.path}]: {json.dumps(response_data, indent=2, ensure_ascii=False)}"
        
        getattr(logger, log_level)(log_message)
        
        return response
    
    def get_client_ip(self, request):
        """
        Obtiene la IP real del cliente considerando proxies
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def sanitize_sensitive_data(self, data):
        """
        Oculta campos sensibles en los logs
        """
        if not isinstance(data, dict):
            return data
            
        sensitive_fields = ['password', 'token', 'secret', 'key', 'authorization']
        sanitized = data.copy()
        
        for field in sensitive_fields:
            for key in list(sanitized.keys()):
                if field.lower() in key.lower():
                    sanitized[key] = '***HIDDEN***'
        
        return sanitized