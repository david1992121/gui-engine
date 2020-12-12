from .serializers import OrderSerializer

# use channel
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_call(order, receiver_ids, call_event):
    channel_layer = get_channel_layer()
    for receiver_id in receiver_ids:
        async_to_sync(channel_layer.group_send)(
            "chat_{}".format(receiver_id),
            { "type": "call.send", "content": OrderSerializer(order).data, "event": call_event }
        )

def send_call_type(mode, receiver_ids):
    channel_layer = get_channel_layer()
    for receiver_id in receiver_ids:
        async_to_sync(channel_layer.group_send)(
            "chat_{}".format(receiver_id),
            { "type": "call_type.send", "content": mode}
        )

def send_room_event(event, room):
    channel_layer = get_channel_layer()
    for user in room.users.all():
        async_to_sync(channel_layer.group_send)(
            "chat_{}".format(user.id),
            { "type": "room_event.send", "content": event}
        )

def send_applier(order_id, room_id, guest_id):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "chat_{}".format(guest_id),
        { "type": "applier.send", "content": { "order": order_id, "room": room_id } }
    )
