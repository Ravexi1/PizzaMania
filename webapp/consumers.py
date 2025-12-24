import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from django.contrib.auth import get_user_model
from django.core.cache import cache
import time


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs'].get('chat_id')
        self.group_name = f'chat_{self.chat_id}'
        self.rate_limit_key = None  # will be set based on user

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

            # Rate limiting для WebSocket
            user_key = str(user_id) if user_id else self.scope.get('client', ['unknown'])[0]
            if await self._check_rate_limit(user_key):
                await self.send(text_data=json.dumps({
                    'error': 'Слишком много сообщений. Подождите немного.'
                }))
                return

            msg, was_inactive = await self._create_message(text, user_id, user_name)

            payload = {
                'type': 'chat.message',
                'message': msg.text,
                'sender_name': msg.sender_name or '',
                'is_system': msg.is_system,
                'created_at': msg.created_at.isoformat(),
            }
            await self.channel_layer.group_send(self.group_name, payload)

            try:
                # Notify CRM about updates and possible reopen
                chat_data = await self._get_chat_data(msg.chat.id)
                if was_inactive:
                    await self.channel_layer.group_send('crm', {
                        'type': 'chat.reopened',
                        'chat': chat_data,
                    })
                else:
                    # Send new chat notification to operators
                    await self.channel_layer.group_send('crm', {
                        'type': 'new.chat',
                        'chat': chat_data,
                    })
                # Always send chat updated notification
                await self.channel_layer.group_send('crm', {
                    'type': 'chat.updated',
                    'chat_id': msg.chat.id,
                    'last_message': msg.text[:200],
                    'last_message_at': msg.created_at.isoformat(),
                })
            except Exception:
                pass

    @database_sync_to_async
    def _check_rate_limit(self, user_key):
        """Проверка rate limit: 10 сообщений в минуту"""
        key = f"rl:ws_chat:{user_key}:{self.chat_id}"
        try:
            count = cache.get(key) or 0
            if count >= 10:
                return True
            cache.set(key, count + 1, timeout=60)
        except Exception:
            pass
        return False

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
        was_inactive = not chat.is_active
        if was_inactive:
            chat.is_active = True
            chat.save(update_fields=['is_active'])
        m = Message.objects.create(
            chat=chat,
            sender_user=user,
            sender_name=user_name or (user.get_full_name() if user else ''),
            text=text
        )
        return m, was_inactive

    @database_sync_to_async
    def _get_chat_data(self, chat_id):
        """Get chat data for notifications"""
        chat = Chat.objects.select_related('operator', 'user').get(id=chat_id)
        last_msg = chat.messages.order_by('-created_at').first()
        return {
            'id': chat.id,
            'user_name': chat.user_name or (chat.user.get_username() if chat.user else 'Гость'),
            'last_message': last_msg.text[:200] if last_msg else '',
            'last_message_at': last_msg.created_at.isoformat() if last_msg else None,
            'operator': chat.operator and {
                'id': chat.operator.id,
                'username': chat.operator.username,
                'first_name': chat.operator.first_name,
            },
            'is_active': chat.is_active,
        }

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event.get('message'),
            'sender_name': event.get('sender_name'),
            'sender_user_id': event.get('sender_user_id'),
            'is_system': event.get('is_system', False),
            'created_at': event.get('created_at', ''),
        }))
