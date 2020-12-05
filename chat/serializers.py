"""
Serializers for Chat
"""
from django.db.models import Count
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ListField
from rest_framework.serializers import ListSerializer

# accounts app
from accounts.serializers.auth import MediaImageSerializer
from accounts.serializers.member import MainInfoSerializer
from accounts.models import Media, Member

# basics app
from basics.serializers import GiftSerializer, LocationSerializer

# app
from .models import AdminNotice, Room, Message, Notice


def file_validator(file):
    max_file_size = 1024 * 1024 * 100  # 100MB

    if file.size > max_file_size:
        raise serializers.ValidationError(_('Max file size is {} and your file size is {}'.
                                            format(max_file_size, file.size)))


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
            'id', 'content', 'user_id', 'from_user_id', 'user', 'from_user',
            'notice_type', 'created_at'
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


# class JoinSerializer(serializers.ModelSerializer):
#     """
#     Join Serializer
#     """
#     user = MainInfoSerializer(read_only=True)

#     class Meta:
#         fields = ('started_at', 'is_extended',
#                   'is_fivepast', 'ended_at', 'user')
#         model = Join


class RoomSerializer(serializers.ModelSerializer):
    """
    Room Serializer
    """
    users = MainInfoSerializer(read_only=True, many=True)
    # joins = JoinSerializer(read_only=True, many=True)
    unread = serializers.IntegerField(read_only=True)
    last_sender = MainInfoSerializer(read_only=True)
    user_ids = ListField(
        child = serializers.IntegerField(), write_only = True
    )
    last_sender_id = serializers.IntegerField(write_only = True)

    class Meta:
        model = Room
        fields = (
            'id',
            'is_group',
            'last_message',
            'users',
            'last_sender',
            'room_type',
            'title',
            # 'joins',
            'unread',
            'created_at',
            'updated_at',
            'user_ids',
            'last_sender_id'
        )

    def create(self, validated_data):
        user_ids = validated_data.pop('user_ids')
        last_sender_id = validated_data.pop('last_sender_id')

        # check if room already exists
        queryset = Room.objects.annotate(count = Count('users'))
        room_type = validated_data['room_type']

        if room_type == "private" or room_type == "random":
            queryset = queryset.filter(count = len(user_ids))
            for user_id in user_ids:
                queryset = queryset.filter(users__pk = user_id)
            queryset = queryset.filter(title = validated_data['title'], room_type = room_type)
        
        elif room_type == "system" or room_type == "admin":
            queryset = queryset.filter(count = 2).filter(users__pk = user_ids[0]).filter(
                users__pk = Member.objects.get(is_superuser = True, username = room_type
            ).id).filter(room_type = room_type)
        if queryset.count() > 0:
            raise serializers.ValidationError({'room': 'Room already exists'})        

        room = Room.objects.create(**validated_data)
        room.users.set(user_ids)
        room.last_sender = Member.objects.get(pk = last_sender_id)

        if room.room_type == "admin":
            room.users.add(Member.objects.get(is_superuser = True, username = "admin"))
        elif room.room_type == "system":
            room.users.add(Member.objects.get(is_superuser = True, username = "system"))
        
        return room

class MessageSerializer(serializers.ModelSerializer):
    """
    Message Serializer
    """
    media_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    medias = MediaImageSerializer(read_only = True, many=True)
    gift_id = serializers.IntegerField(required=False, write_only=True)
    gift = GiftSerializer(read_only = True)
    room = RoomSerializer(read_only = True)
    room_id = serializers.IntegerField(write_only = True, required = False)
    sender = MainInfoSerializer(read_only = True)
    sender_id = serializers.IntegerField(write_only = True, required = False)
    receiver = MainInfoSerializer(read_only = True)

    class Meta:
        model = Message
        fields = (
            'id',
            'content',
            'media_ids',
            'medias',
            'gift_id',
            'gift',
            'is_read',
            'room',
            'sender',
            'receiver',
            'is_notice',
            'is_like',
            'room',
            'room_id',
            'sender_id',
            'created_at'
        )
    
class AdminNoticeSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    location_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        fields = ('id', 'title', 'content', 'location',
                  'location_id', 'created_at', 'updated_at')
        model = AdminNotice


class FileListSerializer(serializers.Serializer):
    media = serializers.ListField(
        child=serializers.FileField(max_length=100000,
                                    allow_empty_file=False, use_url=False, validators=[file_validator])
    )

    def create(self, validated_data):
        media_source = validated_data.pop('media')

        return_array = []
        for img in media_source:
            media_image = Media.objects.create(uri=img)
            return_array.append(media_image.id)

        return return_array

class AdminMessageSerializer(serializers.Serializer):
    content = serializers.CharField()
    media_ids = serializers.ListField(
        child = serializers.IntegerField()
    )
    receiver_ids = serializers.ListField(
        child = serializers.IntegerField()
    )
