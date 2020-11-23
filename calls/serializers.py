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
    user = MainInfoSerializer(read_only = True)
    user_id = serializers.IntegerField(write_only = True)

    class Meta:
        fields = ('id', 'invoice_type', 'amount', 'reason', 'order', 'user', 'updated_at', 'user_id')
        model = Invoice

    def create(self, validated_data):
        user = Member.objects.get(pk = validated_data['user_id'])
        user.point = user.point + validated_data['amount']
        user.save()
        return super(InvoiceSerializer, self).create(validated_data)
        