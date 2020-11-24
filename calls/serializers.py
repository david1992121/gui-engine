from calls.models import Invoice, Order
from rest_framework import serializers
from basics.serializers import LocationSerializer, CostplanSerializer
from accounts.serializers.member import MainInfoSerializer
from accounts.models import Member
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

class InvoiceSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only = True)
    giver = MainInfoSerializer(read_only = True)
    taker = MainInfoSerializer(read_only = True)
    giver_id = serializers.IntegerField(write_only = True, required = False)
    taker_id = serializers.IntegerField(write_only = True, required = False)

    class Meta:
        fields = (
            'id', 'invoice_type', 'give_amount', 'reason', 'order', 'giver', 'taker', 
            'take_amount', 'updated_at', 'giver_id', 'taker_id')
        model = Invoice

    def create(self, validated_data):
        taker = Member.objects.get(pk = validated_data['taker_id'])
        taker.point = taker.point + validated_data['take_amount']
        taker.save()
        return super(InvoiceSerializer, self).create(validated_data)
        