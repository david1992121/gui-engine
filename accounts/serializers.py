from django.contrib.auth import authenticate
from django.conf import settings
from django.utils import timezone

from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.serializers import JSONWebTokenSerializer

from drf_extra_fields.fields import Base64ImageField
from .models import Member, Media


class EmailRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, max_length=30)


class SNSAuthorizeSerializer(serializers.Serializer):
    code = serializers.CharField()


class EmailJWTSerializer(JSONWebTokenSerializer):
    username_field = 'email'

    def get_token(self, object):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(object)
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
        curMediaImage = Media.objects.create(**validated_data)
        curMediaImage.image = image
        curMediaImage.save()
        return True


class MemberSerializer(serializers.ModelSerializer):
    avatars = MediaImageSerializer(read_only=True, many=True)

    class Meta:
        fields = ('id', 'email', 'nickname', 'birthday',
                  'avatars', 'is_registered')
        model = Member
