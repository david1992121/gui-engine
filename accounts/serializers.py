from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from django.contrib.auth import authenticate
from django.conf import settings
from django.utils import timezone
from drf_extra_fields.fields import Base64ImageField
from .models import Member

class EmailRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length = 6, max_length = 30)

