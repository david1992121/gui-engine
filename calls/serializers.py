from calls.models import Order
from basics.models import Location
from rest_framework import serializers
from basics.serializers import LocationSerializer, CostplanSerializer
from accounts.serializers.member import MainInfoSerializer

class OrderSerializer(serializers.ModelSerializer):
    user = MainInfoSerializer()
    joined = MainInfoSerializer(many = True)
    parent_location = LocationSerializer()
    location = LocationSerializer()
    cost_plan = CostplanSerializer()

    class Meta:
        fields = (
            'status', 'reservation', 'place', 'user', 'joined', 'parent_location',
            'meet_time', 'meet_time_iso', 'time_other', 'location', 'location_other',
            'person', 'period', 'cost_plan', 'situations', 'desired', 'is_private',
            'created_at',
        )
        model = Order
