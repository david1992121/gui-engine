from accounts.serializers.auth import MemberSerializer
from .serializers.member import GeneralInfoSerializer

# use channel
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import timedelta
from dateutil.parser import parse
import pytz

def send_present(cast, event, guest_ids):
    channel_layer = get_channel_layer()
    for receiver_id in guest_ids:
        async_to_sync(channel_layer.group_send)(
            "chat_{}".format(receiver_id),
            { "type": "cast_present.send", "content": { "cast": GeneralInfoSerializer(cast).data, "event": event }}
        )

def send_user(cast):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "chat_{}".format(cast.id),
        { "type": "user.send", "content": MemberSerializer(cast).data }
    )

def get_edge_time(cur_date_str, cur_type):
    if cur_type == "from":
        cur_date = parse(cur_date_str)
        date_val = cur_date.astimezone(pytz.timezone('Asia/Tokyo'))
        date_val = date_val.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        return date_val
    else:
        cur_date = parse(cur_date_str)
        date_val = cur_date.astimezone(pytz.timezone('Asia/Tokyo'))
        date_val = date_val + timedelta(days = 1)
        date_val = date_val.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        return date_val