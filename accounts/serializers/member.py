"""
Serializers for Member
"""

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from rest_framework.pagination import PageNumberPagination
from drf_extra_fields.fields import Base64ImageField
from accounts.models import Media, Tweet, Member
from accounts.serializers.auth import MediaImageSerializer
from datetime import datetime
from rest_framework.response import Response


def file_validator(file):
    max_file_size = 1024 * 1024 * 1  # 1MB

    if file.size > max_file_size:
        raise serializers.ValidationError(_('Max file size is {} and your file size is {}'.
                                            format(max_file_size, file.size)))


class InitialInfoRegisterSerializer(serializers.Serializer):
    media = serializers.FileField(max_length=1000000, allow_empty_file=False, use_url=False,
                                  validators=[file_validator], write_only=True)
    nickname = serializers.CharField()
    birthday = serializers.CharField()

    def update(self, instance, validated_data):
        # save media
        image = validated_data.pop('media')
        media_image = Media.objects.create(uri=image)

        # save user
        instance.nickname = validated_data['nickname']
        instance.birthday = validated_data['birthday']
        instance.avatars.add(media_image)
        instance.is_registered = True
        instance.save()

        return instance

class MainInfoSerializer(serializers.ModelSerializer):
    avatars = MediaImageSerializer(read_only=True, many=True)

    class Meta:
        fields = (
            'id',
            'nickname',
            'birthday',
            'avatars',
            'role'
        )
        model = Member

class TweetSerializer(serializers.ModelSerializer):
    medias = serializers.ListField(
        child = serializers.FileField( max_length = 100000,
            allow_empty_file=False, use_url=False, validators=[file_validator] )
        , write_only = True
    )
    likers = serializers.SerializerMethodField()
    user = MainInfoSerializer()
    user_id = serializers.IntegerField(write_only = True)
    class Meta:
        fields = ("id", "content", "images", "user", "likers", "created_at", "medias", "user_id")
        model = Tweet

    def get_likers(self, obj):
        likers_id = obj.tweet_likers.all().order_by('-created_at').values_list('liker')
        like_users = MainInfoSerializer(Member.objects.filter(id__in = likers_id, is_registered = True), many = True)
        return like_users.data

    def create(self, validated_data):
        media_ids = []
        user_id = validated_data.pop('user_id')
        if 'medias' in validated_data.keys():
            media_images = validated_data.pop('medias')
            for media in media_images:
                new_media = Media.objects.create(uri = media)
                media_ids.append(new_media.id)
        
        newTweet = self.objects.create(**validated_data)
        newTweet.user = Member.objects.get(pk = user_id)
        newTweet.images.set(media_ids)
        newTweet.save()

class TweetPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):        
        return Response(data)