"""
Serializers for Auth
"""

from django.utils import timezone

from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.serializers import JSONWebTokenSerializer

from drf_extra_fields.fields import Base64ImageField
from accounts.models import Member, Media, Detail, TransferInfo, Friendship
from basics.serializers import ClassesSerializer, LevelsSerializer, LocationSerializer, SettingSerializer, ChoiceSerializer


class EmailRegisterSerializer(serializers.Serializer):
    """Serializer for Email Register"""
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, max_length=30)
    inviter_code = serializers.CharField(required=False, allow_blank=True)
    nickname = serializers.CharField()
    birthday = serializers.CharField(required=False, allow_blank=True)


class SNSAuthorizeSerializer(serializers.Serializer):
    code = serializers.CharField()
    inviter_code = serializers.CharField(required=False, allow_blank=True)


class AdminEmailJWTSerializer(JSONWebTokenSerializer):
    username_field = 'username'

    def get_token(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

    def validate(self, attrs):
        credentials = {
            'username': '',
            'password': attrs.get("password")
        }

        user_obj = Member.objects.filter(
            username=attrs.get("username"), role__lt=0).first()
        if user_obj:
            credentials['username'] = user_obj.username

            if all(credentials.values()):
                if user_obj.check_password(attrs.get('password')):
                    if not user_obj.is_active:
                        msg = "Your account is blocked"
                        raise serializers.ValidationError(msg)
                    else:
                        user_obj.last_login = timezone.now()
                        user_obj.save()
                        return {
                            'token': self.get_token(user_obj),
                            'user': MemberSerializer(user_obj).data
                        }
                else:
                    msg = 'Password is not correct'
                    raise serializers.ValidationError(msg)
            else:
                msg = 'Must include "email" and "password".'
                msg = msg.format(username_field=self.username_field)
                raise serializers.ValidationError(msg)
        else:
            msg = 'Account with this email does not exist'
            raise serializers.ValidationError(msg)


class EmailJWTSerializer(JSONWebTokenSerializer):
    username_field = 'email'

    def get_token(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

    def validate(self, attrs):
        credentials = {
            'email': '',
            'password': attrs.get("password")
        }

        user_obj = Member.objects.filter(email=attrs.get("email")).first()
        if user_obj:
            credentials['email'] = user_obj.email

            if all(credentials.values()):
                if user_obj.check_password(attrs.get('password')):
                    if not user_obj.is_verified:
                        msg = "You did not verify your email address yet"
                        raise serializers.ValidationError(msg)
                    elif not user_obj.is_active:
                        msg = "Your account is blocked"
                        raise serializers.ValidationError(msg)
                    else:
                        user_obj.last_login = timezone.now()
                        user_obj.save()
                        return {
                            'token': self.get_token(user_obj),
                            'user': MemberSerializer(user_obj).data
                        }
                else:
                    msg = 'Password is not correct'
                    raise serializers.ValidationError(msg)
            else:
                msg = 'Must include "email" and "password".'
                msg = msg.format(username_field=self.username_field)
                raise serializers.ValidationError(msg)
        else:
            msg = 'Account with this email does not exist'
            raise serializers.ValidationError(msg)


class MediaImageSerializer(serializers.ModelSerializer):
    uri = Base64ImageField()

    class Meta:
        fields = ('uri', 'id')
        model = Media

    def create(self, validated_data):
        image = validated_data.pop('uri')
        current_media_image = Media.objects.create(**validated_data)
        current_media_image.image = image
        current_media_image.save()
        return True


class DetailSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Detail


class IntroducerSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'nickname', 'inviter_code')
        model = Member


class TransferInfoSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        fields = (
            'id',
            'bank_name',
            'bank_no',
            'site_name',
            'site_no',
            'account_no',
            'account_cat',
            'transfer_name',
            'user_id')
        model = TransferInfo
        extra_kwargs = {
            'bank_no': {'allow_blank': True},
            'site_no': {'allow_blank': True}
        }


class MemberSerializer(serializers.ModelSerializer):
    avatars = MediaImageSerializer(read_only=True, many=True)
    setting = SettingSerializer(read_only=True)
    detail = DetailSerializer(read_only=True)
    cast_status = ChoiceSerializer(read_only=True, many=True)
    introducer = IntroducerSerializer(read_only=True)
    transfer_infos = TransferInfoSerializer(many=True)
    favorites = serializers.SerializerMethodField()
    location = LocationSerializer(read_only=True)
    cast_class = ClassesSerializer(read_only=True)
    guest_level = LevelsSerializer(read_only=True)

    class Meta:
        fields = (
            'id',
            'email',
            'nickname',
            'birthday',
            'avatars',
            'role',
            'point',
            'word',
            'introducer',
            'point_half',
            'video_point_half',
            'is_registered',
            'setting',
            'detail',
            'location',
            'cast_status',
            'transfer_infos',
            'axes_exist',
            'username',
            'inviter_code',
            'favorites',
            'is_superuser',
            'is_present',
            'status',
            'left_at',
            'cast_class',
            'guest_level',
            'back_ratio'
        )
        model = Member

    def get_favorites(self, obj):
        return list(obj.favorites.values_list('favorite_id', flat=True))
