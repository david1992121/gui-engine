from django.core.exceptions import ValidationError
from .models import Invoice, Order, Join, Review, InvoiceDetail
from rest_framework import serializers

from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from basics.models import Location
from basics.serializers import ChoiceSerializer, GiftSerializer, LocationSerializer, CostplanSerializer, ClassesSerializer

from chat.serializers import RoomSerializer

from accounts.serializers.member import GeneralInfoSerializer, MainInfoSerializer
from accounts.models import Member
from .axes import create_axes_payment

class JoinSerializer(serializers.ModelSerializer):
    """
    Join Serializer
    """
    user = GeneralInfoSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only = True)
    order_id = serializers.IntegerField(write_only = True)
    
    class Meta:
        fields = ('id', 'started_at', 'is_extended', 'order_id', 'user_id', 'is_started',
                  'is_ended', 'ended_at', 'user', 'status', 'selection', 'dropped')
        model = Join

class OrderSerializer(serializers.ModelSerializer):
    user = GeneralInfoSerializer(read_only = True)
    target = GeneralInfoSerializer(read_only = True)
    joined = MainInfoSerializer(many = True, read_only = True)
    parent_location = LocationSerializer(read_only = True)
    location = LocationSerializer(read_only = True)
    cost_plan = CostplanSerializer(read_only = True)
    situations = ChoiceSerializer(read_only = True, many = True)
    room = RoomSerializer(read_only = True)

    parent_location_id = serializers.IntegerField(write_only = True)
    user_id = serializers.IntegerField(write_only = True, required = False)
    target_id = serializers.IntegerField(write_only = True, required = False)
    location_id = serializers.IntegerField(write_only = True, required = False)
    cost_plan_id = serializers.IntegerField(write_only = True, required = False)
    situation_ids = serializers.ListField(
        child = serializers.IntegerField(), write_only = True
    )
    room_id = serializers.IntegerField(write_only = True, required = False)
    joins = JoinSerializer(many = True, read_only = True)
    applying = serializers.SerializerMethodField(read_only = True)
    
    class Meta:
        fields = (
            'id', 'status', 'reservation', 'place', 'user', 'joined', 'parent_location',
            'meet_time', 'meet_time_iso', 'time_other', 'location', 'location_other',
            'person', 'period', 'cost_plan', 'situations', 'is_private',
            'created_at', 'updated_at', 'room', 'collect_started_at', 'collect_ended_at',
            'ended_predict', 'ended_at', 'cost_value', 'cost_extended', 'remark',
            'parent_location_id', 'location_id', 'cost_plan_id', 'situation_ids',
            'night_started_at', 'night_ended_at', 'night_fund', 'operator_message', 'joins',
            'final_cost', 'desire_back_ratio', 'desire_cost', 'night_back_ratio', 'applying', 'user_id',
            'target', 'is_cancelled', 'is_accepted', 'is_replied', 'room_id', 'target_id'
        )
        model = Order
        extra_kwargs = {
            'remark': { 'allow_blank': True },
            'operator_message': { 'allow_blank': True },
            'meet_time': { 'allow_blank': True }
        }

    def get_applying(self, obj):
        return obj.joins.count()    

    def create(self, validated_data):        

        location_id = validated_data.pop('location_id')
        situation_ids = validated_data.pop('situation_ids')
        meet_time_iso = validated_data.pop('meet_time_iso')
        
        new_order = Order.objects.create(**validated_data)
        if len(situation_ids) > 0:
            new_order.situations.set(situation_ids)
        if location_id > 0:
            new_order.location = Location.objects.get(pk = location_id)
        
        cur_time = timezone.now()
        new_order.collect_started_at = cur_time
        new_order.collect_ended_at = cur_time + timedelta(minutes=15)
        
        # get cost plan
        if new_order.cost_plan != None:
            new_order.cost_value = new_order.cost_plan.cost
            new_order.cost_extended = new_order.cost_plan.extend_cost

        # ended predict
        # meet_time = parse(meet_time_iso)
        new_order.meet_time_iso = meet_time_iso
        new_order.ended_predict = meet_time_iso + timedelta(hours=new_order.period)

        new_order.night_started_at = "00:00"
        new_order.night_ended_at = "06:00"

        new_order.save()
        return new_order

    def update(self, instance, validated_data):
        situation_ids = validated_data.pop('situation_ids')
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.ended_predict = instance.meet_time_iso + timedelta(hours = instance.period)
        instance.save()
        instance.situations.set(situation_ids)

        return instance

class InvoiceDetailSerializer(serializers.ModelSerializer):
    cast = MainInfoSerializer(read_only = True)
    cast_id = serializers.IntegerField(write_only = True)
    invoice_ids = serializers.ListField(
        child = serializers.IntegerField(), write_only = True
    )
    order_id = serializers.IntegerField(write_only = True)
    
    class Meta:
        fields = ('id', 'invoice_ids', 'extend_point', 'night_point', 'desire_point',
            'total_point', 'cast', 'cast_id', 'created_at', 'cast_point', 'join_time', 'extend_min',
            'cast_extend_point', 'cast_night_point', 'cast_desire_point', 'order_id')
        model = InvoiceDetail

    def create(self, validated_data):
        invoice_ids = validated_data.pop("invoice_ids")
        order_id = validated_data.pop("order_id")
        cur_order = Order.objects.get(pk = order_id)
        invoice_detail = InvoiceDetail.objects.create(**validated_data)
        
        # Invoice create for cast
        invoice_cast = Invoice.objects.create(
            invoice_type = "CALL", taker = invoice_detail.cast, order_id = order_id, take_amount = invoice_detail.cast_point, room = cur_order.room
        )
        cur_cast = invoice_detail.cast
        cur_cast.point += invoice_detail.cast_point

        invoice_ids.append(invoice_cast.id)
        invoice_detail.invoices.set(invoice_ids)

        # cast expire data update
        if invoice_detail.extend_min > 0:
            cur_cast.expire_times += 1
            cur_cast.expire_amount += invoice_detail.extend_min        
        cur_cast.save()

        # guest expire data update
        if invoice_detail.extend_min > 0:
            guest = cur_order.user
            if cur_order.is_private:
                guest = cur_order.user if cur_order.user.role == 1 else cur_order.target
            guest.expire_times += 1
            guest.expire_amount += invoice_detail.extend_min
            guest.save()
        

        admin = Member.objects.get(is_superuser = True, username = "admin")
        Invoice.objects.create(
            invoice_type = "ADMIN", taker = admin, take_amount = invoice_detail.total_point - invoice_detail.cast_point, order_id = order_id, room = cur_order.room
        )
        admin.point += invoice_detail.total_point - invoice_detail.cast_point
        admin.save()

        return invoice_detail
class InvoiceSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only = True)
    giver = MainInfoSerializer(read_only = True)
    taker = MainInfoSerializer(read_only = True)
    giver_id = serializers.IntegerField(write_only = True, required = False)
    taker_id = serializers.IntegerField(write_only = True, required = False)
    details = InvoiceDetailSerializer(many = True, read_only = True)
    order_id = serializers.IntegerField(write_only = True, required = False)
    gift = GiftSerializer(read_only = True)
    room = RoomSerializer(read_only = True)
    room_id = serializers.IntegerField(write_only = True, required = False)

    class Meta:
        fields = (
            'id', 'invoice_type', 'give_amount', 'reason', 'order', 'giver', 'taker', 
            'take_amount', 'updated_at', 'giver_id', 'taker_id', 'details', 'order_id', 'gift',
            'room', 'room_id')
        model = Invoice
        extra_kwargs = {
            'reason': { 'allow_blank': True },
        }

    def create(self, validated_data):
        from math import ceil

        if "taker_id" in validated_data.keys():
            try:
                taker = Member.objects.get(pk = validated_data['taker_id'])
            except:
                raise ValidationError("User Not Found")
            taker.point = taker.point + validated_data['take_amount']
            taker.save()
        
        if "giver_id" in validated_data.keys():
            try:
                giver = Member.objects.get(pk = validated_data['giver_id'])
            except Member.DoesNotExist:
                raise ValidationError("User Not Found")
            giver.point = giver.point - validated_data['give_amount']
            giver.point_used += validated_data['give_amount']

            if giver.point < 0:
                auto_charge = ceil( (-giver.point) / 1000) * 1000

                # create axes payment
                if not create_axes_payment(giver, auto_charge): 
                    raise ValidationError('Payment Failed')
                else:
                    Invoice.objects.create(invoice_type = "AUTO", taker = giver, take_amount = auto_charge)
                    giver.point += auto_charge

            giver.save()
        
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

class AdminOrderCreateSerializer(serializers.Serializer):
    order = OrderSerializer(write_only = True)
    notify_cast = serializers.IntegerField(write_only = True)
    notify_guest = serializers.IntegerField(write_only = True)

class ReviewSerializer(serializers.ModelSerializer):
    source = MainInfoSerializer(read_only = True)
    target = MainInfoSerializer(read_only = True)
    source_id = serializers.IntegerField(write_only = True)
    target_id = serializers.IntegerField(write_only = True)
    order = OrderSerializer(read_only = True)
    order_id = serializers.IntegerField(write_only = True, required = False)
    
    class Meta:
        fields = ('source', 'target', 'stars', 'content', 'created_at', 'source_id', 'target_id', 'order', 'order_id')
        model = Review