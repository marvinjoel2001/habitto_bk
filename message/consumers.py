import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message
from user.models import UserProfile

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        room_raw = self.scope['url_route']['kwargs'].get('room_id')
        self.room_id = str(room_raw).replace('_', '-')
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

        try:
            sender_id = int(sender_id)
            receiver_id = int(receiver_id)
        except Exception:
            await self.send(text_data=json.dumps({'error': 'IDs inválidos: sender y receiver deben ser enteros'}))
            return

        canonical_room = f"{min(sender_id, receiver_id)}-{max(sender_id, receiver_id)}"
        if str(self.room_id) != canonical_room:
            await self.send(text_data=json.dumps({
                'error': 'room_id mismatch',
                'expected_room_id': canonical_room,
                'provided_room_id': str(self.room_id)
            }))
            return

        msg = await self._store_message(sender_id, receiver_id, content)

        event = {
            'type': 'chat.message',
            'message': {
                'id': msg['id'],
                'room_id': self.room_id,
                'roomId': self.room_id,
                'sender': sender_id,
                'receiver': receiver_id,
                'content': content,
                'created_at': msg['created_at'],
                'createdAt': msg['created_at'],
                'is_read': False,
            }
        }
        await self.channel_layer.group_send(self.group_name, event)

        receiver_cp = await self._get_counterpart_info(sender_id)
        sender_cp = await self._get_counterpart_info(receiver_id)
        inbox_payload_receiver = {
            'message_id': msg['id'],
            'sender': sender_id,
            'receiver': receiver_id,
            'content': content,
            'created_at': msg['created_at'],
            'counterpart_full_name': receiver_cp['full_name'],
            'counterpart_profile_picture': receiver_cp['profile_picture'],
        }
        inbox_payload_sender = {
            'message_id': msg['id'],
            'sender': sender_id,
            'receiver': receiver_id,
            'content': content,
            'created_at': msg['created_at'],
            'counterpart_full_name': sender_cp['full_name'],
            'counterpart_profile_picture': sender_cp['profile_picture'],
        }
        await self.channel_layer.group_send(f'inbox_{receiver_id}', {
            'type': 'new_inbox_alert',
            'payload': inbox_payload_receiver,
        })
        await self.channel_layer.group_send(f'notifications_{receiver_id}', {
            'type': 'new_inbox_alert',
            'payload': inbox_payload_receiver,
        })
        await self.channel_layer.group_send(f'inbox_{sender_id}', {
            'type': 'new_inbox_alert',
            'payload': inbox_payload_sender,
        })
        await self.channel_layer.group_send(f'notifications_{sender_id}', {
            'type': 'new_inbox_alert',
            'payload': inbox_payload_sender,
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def _store_message(self, sender_id: int, receiver_id: int, content: str):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        m = Message.objects.create(sender=sender, receiver=receiver, content=content, is_read=False)
        return {'id': m.id, 'created_at': m.created_at.isoformat()}

    @database_sync_to_async
    def _get_counterpart_info(self, user_id: int):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return {'full_name': str(user_id), 'profile_picture': None}
        full_name = ((user.first_name or '').strip() + ' ' + (user.last_name or '').strip()).strip() or user.username
        picture_url = None
        try:
            profile = UserProfile.objects.filter(user_id=user_id).first()
            if profile and profile.profile_picture:
                picture_url = profile.profile_picture.url
        except Exception:
            picture_url = None
        return {'full_name': full_name, 'profile_picture': picture_url}

class InboxConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user_id_raw = self.scope['url_route']['kwargs'].get('user_id')
        try:
            self.user_id = int(user_id_raw)
        except Exception:
            return await self.close()
        path = self.scope.get('path', '') or ''
        prefix = 'notifications_' if 'notifications' in path else 'inbox_'
        self.group_name = f'{prefix}{self.user_id}'
        user = self.scope.get('user')
        if user and getattr(user, 'is_authenticated', False) and user.id and int(user.id) != self.user_id:
            return await self.close()
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def new_inbox_alert(self, event):
        payload = event.get('payload') or event
        await self.send(text_data=json.dumps(payload))

    async def inbox_message(self, event):
        payload = event.get('payload') or event
        await self.send(text_data=json.dumps(payload))