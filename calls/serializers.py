from calls.models import Invoice, Order
from rest_framework import serializers
from basics.serializers import ChoiceSerializer, LocationSerializer, CostplanSerializer
from chat.serializers import RoomSerializer
from accounts.serializers.member import MainInfoSerializer
from accounts.models import Member
from django.db.models import Sum, Q
from dateutil.parser import parse
from basics.models import Location, CostPlan
class OrderSerializer(serializers.ModelSerializer):
    user = MainInfoSerializer(read_only = True)
    joined = MainInfoSerializer(many = True, read_only = True)
    parent_location = LocationSerializer(read_only = True)
    location = LocationSerializer(read_only = True)
    cost_plan = CostplanSerializer(read_only = True)
    situations = ChoiceSerializer(read_only = True, many = True)
    desired = MainInfoSerializer(read_only = True, many = True)
    room = RoomSerializer(read_only = True)

    parent_location_id = serializers.IntegerField(write_only = True)
    location_id = serializers.IntegerField(write_only = True)
    cost_plan_id = serializers.IntegerField(write_only = True)
    situation_ids = serializers.ListField(
        child = serializers.IntegerField(), write_only = True
    )

    class Meta:
        fields = (
            'status', 'reservation', 'place', 'user', 'joined', 'parent_location',
            'meet_time', 'meet_time_iso', 'time_other', 'location', 'location_other',
            'person', 'period', 'cost_plan', 'situations', 'desired', 'is_private',
            'created_at', 'updated_at', 'room', 'collect_started_at', 'collect_ended_at',
            'ended_predict', 'ended_at', 'cost_value', 'cost_extended', 'remark',
            'parent_location_id', 'location_id', 'cost_plan_id', 'situation_ids'
        )
        model = Order
        extra_kwargs = {
            'remark': { 'allow_blank': True },
        }

    def create(self, validated_data):
        from django.utils import timezone
        from datetime import datetime, timedelta

        location_id = validated_data.pop('location_id')
        situation_ids = validated_data.pop('situation_ids')
        
        new_order = Order.objects.create(**validated_data)
        if len(situation_ids) > 0:
            new_order.situations.set(situation_ids)
        if location_id > 0:
            new_order.location = Location.objects.get(pk = location_id)
        
        cur_time = timezone.now()
        new_order.collect_started_at = cur_time
        new_order.collect_ended_at = cur_time + timedelta(minutes=15)
        
        # get cost plan
        new_order.cost_value = new_order.cost_plan.cost
        new_order.cost_extended = new_order.cost_plan.extend_cost

        # ended predict
        meet_time = datetime.strptime(new_order.meet_time_iso, "%Y-%m-%d %H:%M:%S")
        new_order.ended_predict = meet_time + timedelta(hours=new_order.period)

        new_order.save()
        return new_order

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

class RankUserSerializer(serializers.ModelSerializer):
    overall_points = serializers.SerializerMethodField()
    call_points = serializers.SerializerMethodField()
    private_times = serializers.SerializerMethodField()
    private_points = serializers.SerializerMethodField()
    public_times = serializers.SerializerMethodField()
    public_points = serializers.SerializerMethodField()
    gift_points = serializers.SerializerMethodField()
    gift_times = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id', 'nickname', 'overall_points', 'call_times', 'call_points', 'overall_points',
            'private_times', 'private_points', 'public_points', 'public_times', 'gift_points',
            'gift_times'
        )
        model = Member

    def get_gave_took(self, obj):
        date_from = self.context.get('from', "")        
        date_to = self.context.get('to', "")
        if obj.role == 1:
            query_set = obj.gave
        else:
            query_set = obj.took
        if date_from != "":
            query_set = query_set.filter(created_at__date__gte = date_from)
        if date_to != "":
            query_set = query_set.filter(created_at__date__lte = date_to)
        return query_set

    def get_overall_points(self, obj):
        if obj.role == 1:
            return self.get_gave_took(obj).aggregate(Sum('give_amount'))['give_amount__sum']
        else:
            return self.get_gave_took(obj).aggregate(Sum('take_amount'))['take_amount__sum']

    def get_call_points(self, obj):
        if obj.role == 1:
            return self.get_gave_took(obj).filter(invoice_type = 'CALL').aggregate(Sum('give_amount'))['give_amount__sum']
        else:
            return self.get_gave_took(obj).filter(invoice_type = 'CALL').aggregate(Sum('take_amount'))['take_amount__sum']
        
    def get_private_times(self, obj):
        if obj.role == 0:
            return self.get_gave_took(obj).filter(invoice_type = "CALL", order__is_private = True).count()
        else:
            return 0

    def get_public_times(self, obj):
        if obj.role == 0:
            return self.get_gave_took(obj).filter(invoice_type = "CALL", order__is_private = False).count()
        else:
            return 0

    def get_private_points(self, obj):
        if obj.role == 0:
            return self.get_gave_took(obj).filter(invoice_type = "CALL", order__is_private = True).aggregate(Sum('take_amount'))['take_amount__sum']
        else: 
            return 0
    
    def get_public_points(self, obj):
        if obj.role == 0:
            return self.get_gave_took(obj).filter(invoice_type = "CALL", order__is_private = False).aggregate(Sum('take_amount'))['take_amount__sum']
        else: 
            return 0

    def get_gift_points(self, obj):
        if obj.role == 1:
            return self.get_gave_took(obj).filter(invoice_type = "GIFT").aggregate(Sum('give_amount'))['give_amount__sum']
        else:
            return self.get_gave_took(obj).filter(invoice_type = "GIFT").aggregate(Sum('take_amount'))['take_amount__sum']

    def get_gift_times(self, obj):
        if obj.role == 1:
            return self.get_gave_took(obj).filter(invoice_type = "GIFT").count()
        else:
            return self.get_gave_took(obj).filter(invoice_type = "GIFT").count()