"""
Serializers for Member
"""

from datetime import datetime
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from dateutil.parser import parse

from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.models import Media, Tweet, Member, TransferApplication, Detail, Review
from basics.serializers import LevelsSerializer, ClassesSerializer, LocationSerializer, ChoiceSerializer
from .auth import DetailSerializer, MediaImageSerializer, MemberSerializer, TransferInfoSerializer

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
            'username',
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

class UserSerializer(serializers.ModelSerializer):
    average_review = serializers.SerializerMethodField()
    five_reviews = serializers.SerializerMethodField()
    introducer = MainInfoSerializer(read_only = True)
    cast_class = ClassesSerializer(read_only = True)
    guest_level = LevelsSerializer(read_only = True)
    location = LocationSerializer(read_only = True)
    detail = DetailSerializer()
    transfer_infos = TransferInfoSerializer(many = True, read_only = True, required = False)
    avatars = MediaImageSerializer(read_only=True, many=True)
    cast_status = ChoiceSerializer(read_only=True, many=True)
    
    detail_id = serializers.IntegerField(write_only = True, required = False)
    location_id = serializers.IntegerField(write_only = True, required = False)
    cast_class_id = serializers.IntegerField(write_only = True, required = False)
    introducer_id = serializers.IntegerField(write_only = True, required = False)
    guest_level_id = serializers.IntegerField(write_only = True, required = False)
    password = serializers.CharField(write_only = True, required = False, allow_blank = True)
    email = serializers.EmailField(required = True)

    class Meta:
        fields = (
            'id', 'nickname', 'cast_class', 'guest_level', 'back_ratio', 'expire_times',
            'call_times', 'expire_amount', 'average_review', 'five_reviews', 'introducer',
            'location', 'email', 'memo', 'guest_started_at', 'cast_started_at', 'last_login', 
            'username', 'is_registered', 'is_active', 'phone_number', 'role', 'is_public', 'detail',
            'birthday', 'transfer_infos', 'location_id', 'cast_class_id', 'introducer_id', 'guest_level_id', 'detail_id',
            'password', 'point_half', 'point', 'presented_at', 'inviter_code', 'avatars', 'social_id',
            'cast_status'
        )
        model = Member
        extra_kwargs = {
            'username': { 'allow_blank': True },
            'memo': { 'allow_blank': True },
            'inviter_code': { 'read_only': True }
        }

    def get_average_review(self, obj):
        from django.db.models import Avg
        average_stars = obj.review_sources.aggregate(Avg('stars'))['stars__avg']
        if average_stars:
            return round(average_stars, 2)
        else:
            return 0

    def get_five_reviews(self, obj):
        return obj.review_sources.filter(stars = 5).count()

    def create(self, validated_data):
        detail = validated_data.pop('detail')
        password = ""
        username = ""
        if 'password' in validated_data.keys():
            password = validated_data.pop('password')

        if 'username' in validated_data.keys():
            username = validated_data.pop('username')

        if password == "":
            raise serializers.ValidationError({ "password" : "password is needed" }) 
        
        new_detail = Detail.objects.create(**detail)
        
        new_user = Member.objects.create(**validated_data)
        if password != "":
            new_user.set_password(password)

        if username != "":
            new_user.username = username
        else:
            new_user.username = "user_{}".format(new_user.id)

        if new_user.role == 1 and new_user.guest_started_at == None:
            new_user.guest_started_at = timezone.now()

        if new_user.role == 0 and new_user.cast_started_at == None:
            new_user.cast_started_at = timezone.now()

        new_user.detail = new_detail
        new_user.inviter_code = getInviterCode()
        new_user.save()
        return new_user

    def update(self, instance, validated_data):
        detail = validated_data.pop('detail')
        cur_detail_id = validated_data.pop('detail_id')

        password = ""
        if 'password' in validated_data.keys():
            password = validated_data.pop('password')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password != "":
            instance.set_password(password)

        # present check
        if instance.role == 0:
            if instance.presented_at == None:
                instance.is_present = False
            else:
                if instance.presented_at < timezone.now():
                    instance.presented_at = None
                    instance.is_present = False
                else:
                    instance.is_present = True

        # sns check
        if instance.social_id != None:
            instance.social_type = 1
        else:
            instance.social_type = 0

        cur_detail = Detail.objects.get(pk = cur_detail_id)
        cur_detail.about = detail['about']
        cur_detail.save()

        instance.detail = cur_detail
        instance.save()
        return instance

def getInviterCode():
    import random
    random_id = ""
    while True:
        random_id = ''.join([str(random.randint(0, 999)).zfill(3) for _ in range(2)])
        if Member.objects.filter(inviter_code = random_id).count() > 0:
            continue
        break
    return random_id

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
    category = serializers.IntegerField(default = 0)

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

    def update(self, instance, validated_data):
        media_ids = []
        user_id = validated_data.pop('user_id')
        if 'medias' in validated_data.keys():
            media_images = validated_data.pop('medias')
            for media in media_images:
                new_media = Media.objects.create(uri=media)
                media_ids.append(new_media.id)

        instance.category = validated_data.pop('category')
        instance.user = Member.objects.get(pk=user_id)
        instance.content = validated_data.pop('content')
        instance.save()
        if len(media_ids) > 0:
            instance.images.set(media_ids)

        return instance


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
            new_user = Member.objects.create(username = username)
            if location_id > 0:
                new_user.location_id = location_id

            if password != "":
                new_user.set_password(password)
            new_user.role = -1
            new_user.is_registered = True
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
    user_id = serializers.IntegerField(write_only = True, required = False)

class AdminPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response({
            'total': Member.objects.filter(role__lt=0, is_superuser=False).count(),
            'results': data
        })

class TransferSerializer(serializers.ModelSerializer):
    user = MemberSerializer()    
    class Meta:
        fields = ('id', 'status', 'location', 'user', 'amount', 'apply_type', 'currency_type', 'point', 'created_at')
        model = TransferApplication

class MediaListSerializer(serializers.Serializer):
    media = serializers.ListField(
        child = serializers.FileField( max_length = 100000,
            allow_empty_file=False, use_url=False, validators=[file_validator] )
    )
    user_id = serializers.IntegerField(required = True)

    def create(self, validated_data):
        media_source = validated_data.pop('media')
        user_id = validated_data.pop('user_id')

        return_array = []    
        for img in media_source:
            media_image = Media.objects.create(uri = img)
            cur_user = Member.objects.get(pk = user_id)
            cur_user.avatars.add(media_image)
            return_array.append(media_image)

        return return_array

class ReviewSerializer(serializers.ModelSerializer):
    source = MainInfoSerializer()
    target = MainInfoSerializer()
    
    class Meta:
        fields = ('source', 'target', 'stars', 'content', 'created_at')
        model = Review
  
