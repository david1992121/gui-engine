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