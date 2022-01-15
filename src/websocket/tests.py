"""Test websocket functionality"""
from django.test import TestCase
from channels.testing import WebsocketCommunicator
from websocket.echo import EchoConsumer
import json

# pylint: disable=all

class TestEchoWebsocket(TestCase):
    async def test_welcome(self):
        expected = "Connected to DelfiTLM websocket"
        communicator = await self._get_communicator(False)
        response = await communicator.receive_from()
        self.assertEqual(response, expected)

    async def test_echo(self):
        message = "Sample test message"
        communicator = await self._get_communicator()
        await communicator.send_to(message)
        response_data = await communicator.receive_from()
        response = json.loads(response_data)
        self.assertEqual(response['context'], "echo")
        self.assertEqual(response['text'], message)

    async def _get_communicator(self, skip_welcome=True):
        communicator = WebsocketCommunicator(EchoConsumer.as_asgi(), "ws/echo/")
        connected, _ = await communicator.connect()
        self.assertEqual(connected, True, "Unable to connect to the websocket!")
        if skip_welcome:
            # Skip the welcome message
            await communicator.receive_from()
        return communicator
