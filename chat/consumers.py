import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from accounts.models import Member
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # status save
        await on_status(int(self.room_name))

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # status save
        await off_status(int(self.room_name))

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'channel': self.channel_name
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'channel': self.channel_name
        }))

    # Send Room
    async def room_send(self, event):
        await self.send(text_data=json.dumps({
            "type": "ROOM",
            "event": event['event'],
            "data": event['content']
        }))

    # Send Call
    async def call_send(self, event):
        await self.send(text_data=json.dumps({
            "type": "CALL",
            "event": event['event'],
            "data": event['content']
        }))

    # Send Call Type
    async def call_type_send(self, event):
        await self.send(text_data=json.dumps({
            "type": "CALLTYPE",
            "data": event['content']
        }))

    # Send Cast Present
    async def cast_present_send(self, event):
        await self.send(text_data=json.dumps({
            "type": "PRESENT",
            "data": event['content']
        }))

    # Send Applier
    async def applier_send(self, event):
        await self.send(text_data=json.dumps({
            "type": "APPLIER",
            "data": event['content']
        }))

    # Send Applier
    async def room_event_send(self, event):
        await self.send(text_data=json.dumps({
            "type": "ROOMEVENTS",
            "data": event['content']
        }))

    # Send User
    async def user_send(self, event):
        await self.send(text_data=json.dumps({
            "type": "USER",
            "data": event['content']
        }))

    # Send Message
    async def message_send(self, event):
        content = event['content']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "type": "MESSAGE",
            "data": content
        }))


# user status on
@sync_to_async
def on_status(user_id):
    # status save
    try:
        member = Member.objects.get(pk=user_id)
        member.status = True
        member.save()
    except Member.DoesNotExist:
        pass

# user status off


@sync_to_async
def off_status(user_id):
    try:
        member = Member.objects.get(pk=user_id)
        member.status = False
        member.left_at = timezone.now()
        member.save()
    except Member.DoesNotExist:
        return
