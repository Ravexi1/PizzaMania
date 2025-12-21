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
