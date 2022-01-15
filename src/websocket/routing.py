"""Websocket routes"""
from django.urls import path

from . import entry

websocket_urlpatterns = [
    path('ws/entry/', entry.Consumer.as_asgi()),
]
