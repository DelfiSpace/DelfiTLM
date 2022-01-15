"""Websocket routes"""
from django.urls import path

from . import echo

websocket_urlpatterns = [
    path('ws/echo/', echo.EchoConsumer.as_asgi()),
]
