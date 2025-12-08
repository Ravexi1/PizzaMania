"""
ASGI config for PizzaMania project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from django.conf import settings
try:
    # ASGIStaticFilesHandler serves static files during development when DEBUG=True
    from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
except Exception:
    ASGIStaticFilesHandler = None
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PizzaMania.settings')

# СНАЧАЛА инициализируем Django
django_asgi_app = get_asgi_application()

# In development, wrap the ASGI app with Django's ASGIStaticFilesHandler
# so an ASGI server (daphne/uvicorn) can serve static files without a
# separate static server. Only do this when DEBUG is True and the
# handler is available.
if settings.DEBUG and ASGIStaticFilesHandler:
    django_asgi_app = ASGIStaticFilesHandler(django_asgi_app)

# И только ПОТОМ импортируем всё, что тянет модели
import webapp.routing

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            webapp.routing.websocket_urlpatterns
        )
    ),
})
