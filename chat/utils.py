from django.dispatch.dispatcher import receiver
from accounts.models import Member
from .models import Room, Message
from .serializers import RoomSerializer, MessageSerializer
import pytz

# use channel
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from calls.utils import send_call

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
            { "type": "room.send", "content": RoomSerializer(room).data, "event": "create" }
        )
    else:
        room = Room.objects.filter(users__id = receiver_id, room_type = room_type).first()

    # set room last message
    if message_content != "":
        room.last_message = message_content
    else:
        room.last_message = "『画像』"
    room.save()

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
        self_message.medias.set(media_ids)
        cur_message.medias.set(media_ids)

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
    self_message.medias.set(media_ids)

    # set room last message
    if message_content != "":
        room.last_message = message_content
    else:
        room.last_message = "『画像』"
    room.save()

    for room_member in room.users.all():
        if not room_member.is_superuser:
            # message create
            cur_message = Message.objects.create(content = message_content, 
                room = room, sender = sender, receiver = room_member, follower = self_message, is_read = is_read)

            # send via websocket
            async_to_sync(channel_layer.group_send)(
                "chat_{}".format(room_member.id),
                { "type": "message.send", "content": MessageSerializer(cur_message).data }
            )
            cur_message.medias.set(media_ids)

    return self_message

def send_room_to_users(room, receiver_ids, event_str):
    channel_layer = get_channel_layer()
    for user_id in receiver_ids:
        async_to_sync(channel_layer.group_send)(
            "chat_{}".format(user_id),
            { "type": "room.send", "content": RoomSerializer(room).data, "event": event_str }
        )

def send_message_to_user(message, receiver_id):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "chat_{}".format(receiver_id),
        { "type": "message.send", "content": MessageSerializer(message).data }
    )

def send_notice_to_room(room, message, is_notice = True, cast_id = 0):
    system_user = Member.objects.get(username = "system", is_superuser = True)
    self_message = Message.objects.create(content = message, room = room, sender = system_user, receiver = system_user, is_read = True)

    for receiver in room.users.all():
        if cast_id == 0 or (cast_id > 0 and receiver.id == cast_id):
            new_message = Message.objects.create(
                content = message, room = room, sender = system_user, receiver = receiver, is_read = False, 
                is_notice = is_notice, follower = self_message
            )
            send_message_to_user(new_message, receiver.id)

def create_room(order, cast_ids):
    # create new room and message           
    user_ids = [order.user.id]
    user_ids = user_ids + cast_ids

    new_message = "おめでとうございます♪ \n \
        マッチングが確定しました♪ \n \
        ゲストさんはキャストさんへお店の場所を教えてあげて下さい。\n \
        キャストさんはゲストさんへ到着予定時間をお伝え下さい。\n \
        それでは素敵な時間をお過ごしください。"
    location_name = order.location.name if order.location != None else order.location_other
    date_str = order.meet_time_iso.astimezone(pytz.timezone("Asia/Tokyo")).strftime("%Y{0}%m{1}%d{2}%H{3}%M{4}").format(*"年月日時分")
    room_title = "合流：{0} {1} キャスト{2}人".format(location_name, date_str, order.person)
    new_room = Room.objects.create(
        last_message = new_message, room_type = "public", title = room_title, 
        is_group = True, last_sender = Member.objects.get(username = "system"), status = 2)
    new_room.users.set(user_ids)    

    send_room_to_users(new_room, user_ids, "create")
    room_id = new_room.id

    # send notice to room members
    send_notice_to_room(new_room, new_message, False)

    # change order status into confirm state
    if order.status < 3:
        order.status = 3
    order.room = new_room
    order.save()

    # send order remove to casts
    user_ids.remove(order.user.id)
    send_call(order, user_ids, "delete")

    return room_id