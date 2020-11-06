from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework.pagination import PageNumberPagination
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework.response import Response

from .models import Location, CastClass, Choice, GuestLevel, ReceiptSetting, Banner
from drf_extra_fields.fields import Base64ImageField
class LocationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        fields = ('id', 'name', 'parent', 'order', 'shown')        
        model = Location
    
    def create(self, validated_data):
        validated_data.pop('id')
        return Location.objects.create(**validated_data)

class ClassesSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'color', 'point', 'updated_at')
        model = CastClass

class LevelsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'color', 'point', 'updated_at')
        model = GuestLevel

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'category', 'subcategory', 'order', 'score', 
        'call_shown', 'cast_shown', 'customer_shown', 'sub_one')
        model = Choice

class ChoicePagination(PageNumberPagination):
    page_size = 20

    def get_paginated_response(self, data):
        return Response({
            'total': Choice.objects.count(),
            'results': data
        })

class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'company_name', 'postal_code', 'address', 'building', 'phone_number', 'charger')
        model = ReceiptSetting
        
class BannerSerializer(serializers.ModelSerializer):
    banner_image = Base64ImageField(required = False)
    main_image = Base64ImageField(required = False)
    class Meta:
        fields = ('id', 'name', 'banner_image', 'main_image', 'category', 'updated_at')
        model = Banner

    def create(self, validated_data):
        banner_img = None
        main_img = None
        if "banner_image" in validated_data.keys():
            banner_img = validated_data.pop("banner_image")
            
        if "main_image" in validated_data.keys():    
            main_img = validated_data.pop("main_image")

        new_banner = Banner.objects.create(**validated_data)
        new_banner.banner_image = banner_img
        new_banner.main_image = main_img
        new_banner.save()
        return new_banner

    def update(self, instance, validated_data):
        banner_img = None
        main_img = None
        if "banner_image" in validated_data.keys():
            banner_img = validated_data.pop("banner_image")
            
        if "main_image" in validated_data.keys():    
            main_img = validated_data.pop("main_image")

        instance.update(**validated_data)
        instance.banner_image = banner_img
        instance.main_image = main_img
        instance.save()
        return instance

        