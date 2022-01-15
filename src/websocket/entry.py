import json
from channels.generic.websocket import WebsocketConsumer

class Consumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.send("Connected to DelfiTLM websocket")

    def disconnect(self, code):
        return super().disconnect(code)

    def receive(self, text_data=None, bytes_data=None):
        print(text_data)
        self.send(json.dumps({
            'context': 'echo',
            'text': text_data
        }))
