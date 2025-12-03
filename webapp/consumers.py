import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from django.contrib.auth import get_user_model


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs'].get('chat_id')
        self.group_name = f'chat_{self.chat_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
        except Exception:
            return

        action = data.get('action')
        if action == 'send':
            text = data.get('text', '').strip()
            user_id = data.get('user_id')
            user_name = data.get('user_name')
            if not text:
                return

            # ТУТ ИЗМЕНЕНИЕ: без второй обёртки
            msg = await self._create_message(text, user_id, user_name)

            payload = {
                'type': 'chat.message',
                'message': msg.text,
                'sender_name': msg.sender_name or '',
                'is_system': msg.is_system,
                'created_at': msg.created_at.isoformat(),
            }
            await self.channel_layer.group_send(self.group_name, payload)

    @database_sync_to_async
    def _create_message(self, text, user_id, user_name):
        user = None
        if user_id:
            try:
                User = get_user_model()
                user = User.objects.filter(id=user_id).first()
            except Exception:
                user = None
        chat = Chat.objects.get(id=self.chat_id)
        m = Message.objects.create(
            chat=chat,
            sender_user=user,
            sender_name=user_name or (user.get_full_name() if user else ''),
            text=text
        )
        return m

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event.get('message'),
            'sender_name': event.get('sender_name'),
            'is_system': event.get('is_system', False),
            'created_at': event.get('created_at', '')
        }))
