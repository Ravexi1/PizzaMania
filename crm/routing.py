from django.urls import path
from .consumers import CrmNotificationsConsumer

websocket_urlpatterns = [
    path('ws/crm/', CrmNotificationsConsumer.as_asgi()),
]
