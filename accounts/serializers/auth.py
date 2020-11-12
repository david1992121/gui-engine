"""
Serializers for Auth
"""

from basics.models import Setting
from django.utils import timezone

from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.serializers import JSONWebTokenSerializer

from drf_extra_fields.fields import Base64ImageField
from accounts.models import Member, Media, Detail
from basics.serializers import SettingSerializer, ChoiceSerializer


class EmailRegisterSerializer(serializers.Serializer):
    """Serializer for Email Register"""
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, max_length=30)


class SNSAuthorizeSerializer(serializers.Serializer):
    code = serializers.CharField()

class AdminEmailJWTSerializer(JSONWebTokenSerializer):
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

        user_obj = Member.objects.filter(email=attrs.get("email"), role__lt = 0).first()
        if user_obj:
            credentials['email'] = user_obj.email

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

class MemberSerializer(serializers.ModelSerializer):
    avatars = MediaImageSerializer(read_only=True, many=True)
    setting = SettingSerializer(read_only = True)
    detail = DetailSerializer(read_only = True)
    choice = ChoiceSerializer(read_only=True, many=True)
    class Meta:
        fields = (
            'id',
            'email',
            'nickname',
            'birthday',
            'avatars',
            'role',
            'word',
            'point_half',
            'video_point_half',
            'is_registered',
            'setting',
            'detail',
            'choice'
        )
        model = Member
