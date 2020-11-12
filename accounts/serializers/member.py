"""
Serializers for Member
"""

from datetime import datetime

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.models import Media, Tweet, Member
from basics.serializers import LevelsSerializer, ClassesSerializer, LocationSerializer
from .auth import MediaImageSerializer, DetailSerializer


def file_validator(file):
    max_file_size = 1024 * 1024 * 100  # 100MB

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
        if instance.role == 1:
            instance.guest_started_at = timezone.now()
        elif instance.role == 0:
            instance.cast_started_at = timezone.now()
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
            'role',
            'point'
        )
        model = Member


class GeneralInfoSerializer(serializers.ModelSerializer):
    avatars = MediaImageSerializer(read_only=True, many=True)
    guest_level = LevelsSerializer(read_only=True)
    cast_class = ClassesSerializer(read_only=True)
    job = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'nickname',
            'birthday',
            'word',
            'job',
            'point_half',
            'status',
            'left_at',
            'avatars',
            'guest_level',
            'cast_class'
        )
        model = Member

    def get_job(self, obj):
        return "" if not obj.detail.job else obj.detail.job


class TweetSerializer(serializers.ModelSerializer):
    medias = serializers.ListField(
        child=serializers.FileField(
            max_length=100000,
            allow_empty_file=False,
            use_url=False,
            validators=[file_validator]
        ),
        write_only=True,
        required=False
    )
    likers = serializers.SerializerMethodField()
    user = MainInfoSerializer(read_only=True)
    images = MediaImageSerializer(read_only=True, many=True)
    user_id = serializers.IntegerField(write_only=True)
    category = serializers.IntegerField(default=0)

    class Meta:
        fields = ("id", "content", "images", "user",
                  "likers", "created_at", "medias", "user_id", "category", "updated_at")
        model = Tweet

    def get_likers(self, obj):
        likers_id = obj.tweet_likers.all().order_by('-created_at').values_list('liker')
        like_users = MainInfoSerializer(Member.objects.filter(
            id__in=likers_id, is_registered=True), many=True)
        return like_users.data

    def create(self, validated_data):
        media_ids = []
        user_id = validated_data.pop('user_id')
        if 'medias' in validated_data.keys():
            media_images = validated_data.pop('medias')
            for media in media_images:
                new_media = Media.objects.create(uri=media)
                media_ids.append(new_media.id)

        new_tweet = Tweet(**validated_data)
        new_tweet.user = Member.objects.get(pk=user_id)
        new_tweet.save()
        new_tweet.images.set(media_ids)

        return new_tweet


class TweetPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response(data)


class AvatarSerializer(serializers.ModelSerializer):
    media = serializers.FileField(
        max_length=1000000, allow_empty_file=False, use_url=False, validators=[file_validator],
        write_only=True, required=False)

    class Meta:
        fields = ('id', 'media')
        model = Media

    def create(self, validated_data):
        uri_img = validated_data.pop('media')
        new_media = Media.objects.create(uri=uri_img)
        return new_media

    def update(self, instance, validated_data):
        uri_img = validated_data.pop('media')
        instance.uri = uri_img
        instance.save()
        return instance


class AvatarChangerSerializer(serializers.Serializer):
    uris = serializers.ListField(
        child=serializers.CharField(),
        write_only=True
    )


class PasswordChange(serializers.Serializer):
    old = serializers.CharField(required=False)
    new = serializers.CharField(required=False)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('nickname', 'birthday', 'word',
                  'point_half', 'video_point_half')
        model = Member


class CastFilterSerializer(serializers.Serializer):
    choices = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    location = serializers.IntegerField()
    nickname = serializers.CharField(required=False)
    cast_class = serializers.IntegerField()
    is_new = serializers.BooleanField()
    point_min = serializers.IntegerField()
    point_max = serializers.IntegerField()
    page = serializers.IntegerField()


class GuestFilterSerializer(serializers.Serializer):
    page = serializers.IntegerField()
    age_min = serializers.IntegerField()
    age_max = serializers.IntegerField()
    nickname = serializers.CharField(required=False)
    salary = serializers.IntegerField()
    favorite = serializers.CharField(required=False)


class AdminSerializer(serializers.ModelSerializer):
    location_id = serializers.IntegerField(write_only=True)
    location = LocationSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        fields = ('id', 'username', 'location', 'location_id', 'password')
        model = Member

    def create(self, validated_data):
        password = ""
        if 'password' in validated_data.keys():
            password = validated_data.pop('password')
        else:
            return serializers.ValidationError("Password is required")

        username = validated_data['username']
        location_id = int(validated_data['location_id'])
        if Member.objects.filter(username=username).count() > 0:
            return serializers.ValidationError("Username already exists")
        else:
            new_user = Member.objects.create(username=username)
            if location_id > 0:
                new_user.location_id = location_id

            if password != "":
                new_user.set_password(password)
            new_user.role = -1
            new_user.save()

            return new_user

    def update(self, instance, validated_data):
        password = ""
        if 'password' in validated_data.keys():
            password = validated_data.pop('password')

        username = validated_data['username']
        location_id = int(validated_data['location_id'])
        if Member.objects.exclude(pk=instance.pk).filter(username=username).count() > 0:
            return serializers.ValidationError({"username": "Username already exists"})
        else:
            instance.username = username
            if location_id > 0:
                instance.location_id = location_id

            if password != "":
                instance.set_password(password)
            instance.save()

            return instance


class ChoiceIdSerializer(serializers.Serializer):
    choice = serializers.ListField(
        child=serializers.IntegerField()
    )


class AdminPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response({
            'total': Member.objects.filter(role__lt=0, is_superuser=False).count(),
            'results': data
        })
