"""
ASGI config for app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from django.urls import path

from channels.routing import ProtocolTypeRouter,URLRouter
from channels.auth import AuthMiddlewareStack
from gui import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

asgi_application = get_asgi_application()
application= ProtocolTypeRouter(
    {
        'http': asgi_application,
        'websocket': AuthMiddlewareStack(
            URLRouter(
            routing.websocket_urlpatterns
        ))
    }
)