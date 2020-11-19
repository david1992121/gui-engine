"""
Serializers for Chat

"""
from basics.serializers import GiftSerializer
from accounts.serializers.auth import MediaImageSerializer
from calls.models import Order
from accounts.serializers.member import MainInfoSerializer
from calls.serializers import OrderSerializer
from rest_framework import serializers
from .models import Room, Message

class RoomSerializer(serializers.ModelSerializer):
    users = MainInfoSerializer(read_only = True, many = True)
    joins = MainInfoSerializer(read_only = True, many = True)
    order = OrderSerializer(read_only = True)    

    class Meta:
        fields = ('is_group', 'last_message', 'users', 'room_type', 'order', 'title', 'joins',)
        model = Room

class MessageSerializer(serializers.ModelSerializer):
    medias = MediaImageSerializer(many = True)
    gift = GiftSerializer()
    sender = MainInfoSerializer()
    receiver = MainInfoSerializer()

    class Meta:
        fields = ('content', 'medias', 'gift', 'is_read', 'sender',
            'receiver', 'is_notice', 'is_like', 'created_at'
        )
        model = Message