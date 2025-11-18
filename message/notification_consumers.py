import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from property.models import Property
from matching.models import Match
from datetime import datetime
from .websocket_logger import log_websocket_connection, log_websocket_disconnection, WebSocketInteractionLogger

class PropertyNotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer para notificaciones de propiedades (likes, matches aceptados)
    """
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')
        self.user = self.scope['user']
        
        # Verificar autenticación
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Verificar que el usuario solo pueda conectarse a su propio canal
        if str(self.user.id) != str(self.user_id):
            await self.close()
            return
            
        self.group_name = f'property_notifications_{self.user_id}'
        
        # Unirse al grupo de notificaciones
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Registrar conexión
        log_websocket_connection(self.user, 'property_notifications')
        
        # Enviar confirmación de conexión
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado a notificaciones de propiedades',
            'timestamp': datetime.now().isoformat()
        }))

    async def disconnect(self, close_code):
        # Registrar desconexión
        if hasattr(self, 'user'):
            log_websocket_disconnection(self.user, 'property_notifications')
        
        # Salir del grupo cuando se desconecta
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        """Manejar mensajes entrantes del cliente"""
        try:
            data = json.loads(text_data or '{}')
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
            elif message_type == 'mark_read':
                # Marcar notificación como leída
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'JSON inválido'
            }))

    # Handlers para mensajes del channel layer
    async def property_like_notification(self, event):
        """Manejar notificaciones de like en propiedades"""
        # Registrar recepción de notificación
        WebSocketInteractionLogger.log_notification_received(
            user_id=self.user.id if hasattr(self, 'user') else None,
            notification_type='property_like',
            data=event
        )
        
        await self.send(text_data=json.dumps({
            'type': 'property_like',
            'property_id': event['property_id'],
            'property_title': event['property_title'],
            'interested_user': event['interested_user'],
            'timestamp': event['timestamp'],
            'notification_id': event['notification_id']
        }))

    async def match_accepted_notification(self, event):
        """Manejar notificaciones de match aceptado"""
        await self.send(text_data=json.dumps({
            'type': 'match_accepted',
            'property_id': event['property_id'],
            'property_title': event['property_title'],
            'property_address': event['property_address'],
            'owner_contact': event['owner_contact'],
            'match_status': event['match_status'],
            'next_steps': event['next_steps'],
            'timestamp': event['timestamp'],
            'notification_id': event['notification_id']
        }))

    async def general_notification(self, event):
        """Manejar notificaciones generales"""
        await self.send(text_data=json.dumps({
            'type': event.get('notification_type', 'general'),
            'message': event['message'],
            'data': event.get('data', {}),
            'timestamp': event['timestamp'],
            'notification_id': event['notification_id']
        }))

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Marcar notificación como leída (placeholder para futura implementación)"""
        # Aquí se podría implementar un modelo de Notification para tracking
        pass


class TenantNotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer específico para notificaciones de inquilinos (match aceptados)
    """
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')
        self.user = self.scope['user']
        
        # Verificar autenticación
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Verificar que el usuario solo pueda conectarse a su propio canal
        if str(self.user.id) != str(self.user_id):
            await self.close()
            return
            
        self.group_name = f'tenant_notifications_{self.user_id}'
        
        # Unirse al grupo de notificaciones
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar confirmación de conexión
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado a notificaciones de inquilino',
            'timestamp': datetime.now().isoformat()
        }))

    async def disconnect(self, close_code):
        # Salir del grupo cuando se desconecta
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        """Manejar mensajes entrantes del cliente"""
        try:
            data = json.loads(text_data or '{}')
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'JSON inválido'
            }))

    async def match_accepted_for_tenant(self, event):
        """Manejar notificaciones de match aceptado específicamente para inquilinos"""
        await self.send(text_data=json.dumps({
            'type': 'match_accepted_by_owner',
            'property_id': event['property_id'],
            'property_title': event['property_title'],
            'property_address': event['property_address'],
            'owner_name': event['owner_name'],
            'owner_contact': event['owner_contact'],
            'match_score': event['match_score'],
            'next_steps': event['next_steps'],
            'timestamp': event['timestamp'],
            'notification_id': event['notification_id']
        }))


# Utility functions para enviar notificaciones
async def send_property_like_notification(channel_layer, property_owner_id, property_id, property_title, interested_user_data):
    """Enviar notificación de like en propiedad"""
    from datetime import datetime
    import uuid
    
    notification_data = {
        'type': 'property_like_notification',
        'property_id': property_id,
        'property_title': property_title,
        'interested_user': interested_user_data,
        'timestamp': datetime.now().isoformat(),
        'notification_id': str(uuid.uuid4())
    }
    
    # Registrar envío de notificación
    WebSocketInteractionLogger.log_notification_sent(
        sender_id=interested_user_data.get('id'),
        recipient_id=property_owner_id,
        notification_type='property_like',
        data=notification_data
    )
    
    await channel_layer.group_send(
        f'property_notifications_{property_owner_id}',
        notification_data
    )


async def send_match_accepted_notification(channel_layer, tenant_user_id, property_data, owner_data, match_data):
    """Enviar notificación de match aceptado"""
    from datetime import datetime
    import uuid
    
    # Notificación para el propietario
    owner_notification = {
        'type': 'match_accepted_notification',
        'property_id': property_data['id'],
        'property_title': property_data['title'],
        'property_address': property_data['address'],
        'owner_contact': owner_data['contact'],
        'match_status': 'accepted',
        'next_steps': [
            'Contactar al inquilino para coordinar visita',
            'Verificar documentación',
            'Coordinar firma de contrato'
        ],
        'timestamp': datetime.now().isoformat(),
        'notification_id': str(uuid.uuid4())
    }
    
    # Notificación específica para el inquilino
    tenant_notification = {
        'type': 'match_accepted_for_tenant',
        'property_id': property_data['id'],
        'property_title': property_data['title'],
        'property_address': property_data['address'],
        'owner_name': owner_data['name'],
        'owner_contact': owner_data['contact'],
        'match_score': match_data['score'],
        'next_steps': [
            'Contactar al propietario para coordinar visita',
            'Preparar documentación necesaria',
            'Coordinar fecha de mudanza'
        ],
        'timestamp': datetime.now().isoformat(),
        'notification_id': str(uuid.uuid4())
    }
    
    # Enviar a ambos canales
    await channel_layer.group_send(
        f'property_notifications_{owner_data["id"]}',
        owner_notification
    )
    
    await channel_layer.group_send(
        f'tenant_notifications_{tenant_user_id}',
        tenant_notification
    )