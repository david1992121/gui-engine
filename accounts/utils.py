from .serializers.member import GeneralInfoSerializer

# use channel
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_present(cast, event, guest_ids):
    channel_layer = get_channel_layer()
    for receiver_id in guest_ids:
        async_to_sync(channel_layer.group_send)(
            "chat_{}".format(receiver_id),
            { "type": "cast_present.send", "content": { "cast": GeneralInfoSerializer(cast).data, "event": event }}
        )