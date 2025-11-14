import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs'].get('room_id')
        self.group_name = f'chat_{self.room_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            payload = json.loads(text_data or '{}')
        except Exception:
            return

        content = (payload.get('content') or '').strip()
        sender_id = payload.get('sender')
        receiver_id = payload.get('receiver')

        if not content or not sender_id or not receiver_id:
            await self.send(text_data=json.dumps({'error': 'Campos requeridos: sender, receiver, content'}))
            return

        msg = await self._store_message(sender_id, receiver_id, content)

        event = {
            'type': 'chat.message',
            'message': {
                'id': msg['id'],
                'room_id': self.room_id,
                'sender': sender_id,
                'receiver': receiver_id,
                'content': content,
                'created_at': msg['created_at'],
            }
        }
        await self.channel_layer.group_send(self.group_name, event)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def _store_message(self, sender_id: int, receiver_id: int, content: str):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        m = Message.objects.create(sender=sender, receiver=receiver, content=content)
        return {'id': m.id, 'created_at': m.created_at.isoformat()}