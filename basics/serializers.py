from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework.pagination import PageNumberPagination
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from .models import Location, CastClass, Choice
from rest_framework.response import Response
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