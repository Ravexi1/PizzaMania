from django.urls import path
from .consumers import CrmNotificationsConsumer, ChatConsumer

websocket_urlpatterns = [
    path('ws/crm/', CrmNotificationsConsumer.as_asgi()),
    path('ws/chat/<int:chat_id>/', ChatConsumer.as_asgi()),
]
