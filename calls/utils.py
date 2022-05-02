from .serializers import OrderSerializer
import pytz
from dateutil.parser import parse
from datetime import timedelta

# use channel
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def send_call(order, receiver_ids, call_event):
    channel_layer = get_channel_layer()
    for receiver_id in receiver_ids:
        async_to_sync(channel_layer.group_send)(
            "chat_{}".format(receiver_id),
            {"type": "call.send", "content": OrderSerializer(order).data, "event": call_event}
        )


def send_call_type(mode, receiver_ids):
    channel_layer = get_channel_layer()
    for receiver_id in receiver_ids:
        async_to_sync(channel_layer.group_send)(
            "chat_{}".format(receiver_id),
            {"type": "call_type.send", "content": mode}
        )


def send_room_event(event, room):
    channel_layer = get_channel_layer()
    for user in room.users.all():
        async_to_sync(channel_layer.group_send)(
            "chat_{}".format(user.id),
            {"type": "room_event.send", "content": event}
        )


def send_applier(order_id, room_id, guest_id, is_exceed=False):
    channel_layer = get_channel_layer()
    async_to_sync(
        channel_layer.group_send)(
        "chat_{}".format(guest_id), {
            "type": "applier.send", "content": {
                "order": order_id, "room": room_id, "exceed": is_exceed}})


def get_edge_time(cur_date_str, cur_type):
    if cur_type == "from":
        cur_date = parse(cur_date_str)
        date_val = cur_date.astimezone(pytz.timezone('Asia/Tokyo'))
        date_val = date_val.replace(hour=0, minute=0, second=0, microsecond=0)
        return date_val
    else:
        cur_date = parse(cur_date_str)
        date_val = cur_date.astimezone(pytz.timezone('Asia/Tokyo'))
        date_val = date_val + timedelta(days=1)
        date_val = date_val.replace(hour=0, minute=0, second=0, microsecond=0)
        return date_val
