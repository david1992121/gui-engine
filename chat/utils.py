from accounts.models import Member
from .models import Room, Message
from .serializers import RoomSerializer, MessageSerializer

# use channel
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_super_message(room_type, receiver_id, message_content, media_ids = []):
    try:
        sender = Member.objects.get(is_superuser = True, username = room_type)
        receiver = Member.objects.get(pk = receiver_id)
    except Member.DoesNotExist:
        return
    except Exception as e:
        print(e)
        return

    # get channel layer
    channel_layer = get_channel_layer()
    
    if Room.objects.filter(users__id = receiver_id, room_type = room_type).count() == 0:
        cur_title = "Gui運営局"
        if room_type == "system":
            cur_title = "システムメッセージ"
        room = Room.objects.create(room_type = room_type, last_message = message_content, title = cur_title)
        room.users.set([sender, receiver])

        # room send via socket
        async_to_sync(channel_layer.group_send)(
            "chat_{}".format(receiver_id),
            { "type": "room.send", "content": RoomSerializer(room).data }
        )
    else:
        room = Room.objects.filter(users__id = receiver_id, room_type = room_type).first()

    # send message
    self_message = Message.objects.create(
        content = message_content, sender = sender, receiver = sender, is_read = True, room = room
    )
    cur_message = Message.objects.create(
        content = message_content, sender = sender, 
        receiver = receiver, room = room,
        follower = self_message
    )
    if len(media_ids) > 0:
        cur_message.media_ids.set(media_ids)

    # message send via socket
    async_to_sync(channel_layer.group_send)(
        "chat_{}".format(receiver_id),
        { "type": "message.send", "content": MessageSerializer(cur_message).data }
    )

def send_super_room(room_id, sender_id, message_content, media_ids = [], is_read = False):
    room = Room.objects.get(pk = room_id)
    sender = Member.objects.get(pk = sender_id)
    channel_layer = get_channel_layer()
    self_message = Message.objects.create(content = message_content, room = room, sender = sender, receiver = sender, is_read = True)
    self_message.media_ids.set(media_ids)

    for room_member in room.users.all():
        if not room_member.is_superuser:
            # message create
            cur_message = Message.objects.create(content = message_content, 
                room = room, sender = sender, receiver = room_member, follower = self_message, is_read = is_read)

            # send via websocket
            async_to_sync(channel_layer.group_send)(
                "chat_{}".format(room_member.id),
                { "type": "room.message", "content": MessageSerializer(cur_message).data }
            )
            cur_message.media_ids.set(media_ids)

    return self_message
