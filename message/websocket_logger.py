import json
import logging
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class WebSocketInteractionLogger:
    """
    Utilidad para registrar interacciones de WebSocket
    """
    
    @staticmethod
    def log_connection(user_id, connection_type, status, details=None):
        """Registrar conexión de WebSocket"""
        log_data = {
            'event_type': 'websocket_connection',
            'user_id': user_id,
            'connection_type': connection_type,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        logger.info(f"WebSocket Connection: {json.dumps(log_data)}")
    
    @staticmethod
    def log_notification_sent(notification_type, sender_id, recipient_id, data):
        """Registrar envío de notificación"""
        log_data = {
            'event_type': 'notification_sent',
            'notification_type': notification_type,
            'sender_id': sender_id,
            'recipient_id': recipient_id,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Notification Sent: {json.dumps(log_data)}")
    
    @staticmethod
    def log_notification_received(user_id, notification_type, data):
        """Registrar recepción de notificación"""
        log_data = {
            'event_type': 'notification_received',
            'user_id': user_id,
            'notification_type': notification_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Notification Received: {json.dumps(log_data)}")
    
    @staticmethod
    def log_error(user_id, error_type, error_message, context=None):
        """Registrar error de WebSocket"""
        log_data = {
            'event_type': 'websocket_error',
            'user_id': user_id,
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        logger.error(f"WebSocket Error: {json.dumps(log_data)}")

# Modelo opcional para persistir interacciones importantes
class WebSocketInteraction(models.Model):
    """
    Modelo para persistir interacciones de WebSocket importantes
    """
    INTERACTION_TYPES = [
        ('connection', 'Conexión'),
        ('notification_sent', 'Notificación Enviada'),
        ('notification_received', 'Notificación Recibida'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='websocket_interactions')
    interaction_type = models.CharField(max_length=50, choices=INTERACTION_TYPES)
    data = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_interaction_type_display()} - {self.timestamp}"

# Funciones helper para usar en los consumers
def log_websocket_connection(user, connection_type):
    """Helper para registrar conexiones"""
    WebSocketInteractionLogger.log_connection(
        user_id=user.id if user.is_authenticated else None,
        connection_type=connection_type,
        status='connected',
        details={'username': user.username if user.is_authenticated else 'anonymous'}
    )

def log_websocket_disconnection(user, connection_type):
    """Helper para registrar desconexiones"""
    WebSocketInteractionLogger.log_connection(
        user_id=user.id if user.is_authenticated else None,
        connection_type=connection_type,
        status='disconnected',
        details={'username': user.username if user.is_authenticated else 'anonymous'}
    )