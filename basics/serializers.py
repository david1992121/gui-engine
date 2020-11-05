from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from .models import Location, CastClass

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
        fields = ('id', 'name', 'color', 'point')
        model = CastClass