from channels.generic.websocket import AsyncJsonWebsocketConsumer


class CrmNotificationsConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.group_name = 'crm'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notify(self, event):
        # event should contain 'type': 'notify', and 'payload'
        await self.send_json(event.get('payload', {}))

    async def chat_assigned(self, event):
        await self.send_json({
            'type': 'chat_assigned',
            'chat_id': event.get('chat_id'),
            'operator_id': event.get('operator_id'),
            'operator_name': event.get('operator_name'),
        })

    async def chat_closed(self, event):
        await self.send_json({
            'type': 'chat_closed',
            'chat_id': event.get('chat_id'),
        })

    async def chat_reopened(self, event):
        await self.send_json({
            'type': 'chat_reopened',
            'chat_id': event.get('chat_id'),
        })

    async def chat_updated(self, event):
        await self.send_json({
            'type': 'chat_updated',
            'chat_id': event.get('chat_id'),
            'last_message': event.get('last_message'),
            'last_message_at': event.get('last_message_at'),
        })

    async def new_chat(self, event):
        """Notify operators about new active chat"""
        await self.send_json({
            'type': 'new_chat',
            'chat': event.get('chat'),
        })

    async def chat_reopened(self, event):
        """Notify operators when inactive chat becomes active again"""
        await self.send_json({
            'type': 'chat_reopened',
            'chat': event.get('chat'),
        })


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time chat updates"""
    
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.user = self.scope['user']
        self.room_group_name = f'chat_{self.chat_id}'
        
        # Add to chat group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        # Also add to crm_chats for all operators to see assignments/closures
        await self.channel_layer.group_add('crm_chats', self.channel_name)
        
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard('crm_chats', self.channel_name)

    async def chat_message(self, event):
        """Handle new message"""
        await self.send_json({
            'type': 'message',
            'text': event['message'],
            'sender_name': event.get('sender_name'),
            'sender_user_id': event.get('sender_user_id'),
            'is_system': event.get('is_system', False),
            'created_at': event.get('created_at'),
        })

    async def chat_assigned(self, event):
        """Handle chat assigned to operator"""
        await self.send_json({
            'type': 'chat_assigned',
            'chat_id': event['chat_id'],
            'operator_id': event['operator_id'],
            'operator_name': event['operator_name'],
        })

    async def chat_closed(self, event):
        """Handle chat closed"""
        await self.send_json({
            'type': 'chat_closed',
            'chat_id': event['chat_id'],
        })
