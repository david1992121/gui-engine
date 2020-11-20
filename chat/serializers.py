"""
Serializers for Chat
"""
from rest_framework import serializers
from accounts.serializers.auth import MediaImageSerializer
from accounts.serializers.member import MainInfoSerializer
from basics.serializers import GiftSerializer
from calls.serializers import OrderSerializer
from chat.models import Room, Message, Notice


class NoticeSerializer(serializers.ModelSerializer):
    """
    Notice Serializer
    """
    user_id = serializers.IntegerField()
    from_user_id = serializers.IntegerField()
    user = MainInfoSerializer(read_only=True)
    from_user = MainInfoSerializer(read_only=True)

    class Meta:
        model = Notice
        fields = (
            'id',
            'content',
            'user_id',
            'from_user_id',
            'user',
            'from_user',
            'notice_type',
            'created_at'
        )
        extra_keywords = {
            'user_id': {
                'write_only': True,
                'required': True
            },
            'from_user_id': {
                'write_only': True,
                'required': True
            }
        }


class RoomSerializer(serializers.ModelSerializer):
    """
    Room Serializer
    """
    users = MainInfoSerializer(read_only=True, many=True)
    joins = MainInfoSerializer(read_only=True, many=True)
    order = OrderSerializer(read_only=True)
    unread = serializers.IntegerField(read_only = True)    

    class Meta:
        model = Room
        fields = (
            'id',
            'is_group',
            'last_message',
            'users',
            'room_type',
            'order',
            'title',
            'joins',
            'unread',
            'updated_at'
        )


class MessageSerializer(serializers.ModelSerializer):
    """
    Message Serializer
    """
    medias = MediaImageSerializer(many=True)
    gift = GiftSerializer()
    sender = MainInfoSerializer()
    receiver = MainInfoSerializer()

    class Meta:
        model = Message
        fields = (
            'content',
            'medias',
            'gift',
            'is_read',
            'sender',
            'receiver',
            'is_notice',
            'is_like',
            'created_at'
        )
