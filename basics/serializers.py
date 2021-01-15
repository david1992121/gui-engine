from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import CostPlan, Gift, Location, CastClass, Choice, GuestLevel, ReceiptSetting, Banner, Setting
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
        fields = ('id', 'name', 'color', 'point', 'updated_at', 'order')
        model = CastClass

class LevelsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'color', 'point', 'updated_at', 'order')
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
    delete_banner = serializers.BooleanField(default = False, write_only = True)
    delete_main = serializers.BooleanField(default = False, write_only = True)
    class Meta:
        fields = ('id', 'name', 'banner_image', 'main_image', 'category', 'created_at', 'updated_at', 'delete_banner', 'delete_main')
        model = Banner
        extra_kwargs = {
            'name': { 'allow_blank' : True }
        }

    def create(self, validated_data):
        validated_data.pop('delete_banner')
        validated_data.pop('delete_main')
        
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
        delete_banner = validated_data['delete_banner']
        delete_main = validated_data['delete_main']
        if "banner_image" in validated_data.keys():
            banner_img = validated_data.pop("banner_image")
            
        if "main_image" in validated_data.keys():    
            main_img = validated_data.pop("main_image")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # delete banner
        if delete_banner:
            instance.banner_image = None
        else:
            if banner_img:
                instance.banner_image = banner_img

        # delete main        
        if delete_main:
            instance.main_image = None
        else:
            if main_img:
                instance.main_image = main_img            

        instance.save()
        return instance

class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'app_footprint', 'ranking_display', 'email_message')
        model = Setting

class GiftSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required = False)
    location = LocationSerializer(required = False)

    class Meta:
        fields = ('id', 'name', 'image', 'location', 'point', 'back', 'is_shown', 'updated_at')
        model = Gift

    def create(self, validated_data):
        # handle image
        gift_img = None
        if 'image' in validated_data.keys():
            gift_img = validated_data.pop('image')

        # handle location
        location = None
        if 'location' in validated_data.keys():
            location_data = validated_data.pop('location')
            location = Location.objects.get(pk = location_data.get('id'))
        new_gift = Gift.objects.create(**validated_data)
        if location:
            new_gift.location = location
        new_gift.image = gift_img
        new_gift.save()
        return new_gift

    def update(self, instance, validated_data):
        gift_img = None
        if 'image' in validated_data.keys():
            gift_img = validated_data.pop('image')
        
        # handle location
        location = None
        if 'location' in validated_data.keys():
            location_data = validated_data.pop('location')
            location = Location.objects.get(pk = location_data.get('id'))

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if gift_img:
            instance.image = gift_img
        instance.location = location
        instance.save()
        return instance

class GiftPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response({
            'total': Gift.objects.count(),
            'results': data
        })

class CostplanSerializer(serializers.ModelSerializer):
    location = LocationSerializer(required = False)

    class Meta:
        fields = ('id', 'name', 'location', 'cost', 'extend_cost', 'created_at', 'updated_at')
        model = CostPlan

    def create(self, validated_data):
        # handle location
        location = None
        if 'location' in validated_data.keys():
            location_data = validated_data.pop('location')
            location = Location.objects.get(pk = location_data.get('id'))
        new_plan = CostPlan.objects.create(**validated_data)
        if location:
            new_plan.location = location
        new_plan.save()
        return new_plan

    def update(self, instance, validated_data):       
        # handle location
        location = None
        if 'location' in validated_data.keys():
            location_data = validated_data.pop('location')
            location = Location.objects.get(pk = location_data.get('id'))
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.location = location
        instance.save()
        return instance

class CostplanPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response({
            'total': CostPlan.objects.count(),
            'results': data
        })
