from django.core.validators import MinLengthValidator
from accounts.serializers.member import UserSerializer
from inspect import formatargvalues
import json, pytz
from datetime import datetime, timedelta

from django.db.models import Sum, Q, Count, F
from django.core.paginator import Paginator, EmptyPage
from django.utils import timezone
from dateutil.parser import parse
from rest_framework.serializers import Serializer
from accounts.views.member import IsAdminPermission, IsCastPermission, IsSuperuserPermission, IsGuestPermission, set_choices

from rest_framework import status
from rest_framework import generics
from rest_framework import mixins
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import *
from .utils import get_edge_time, send_call, send_applier, send_call_type, send_room_event
from chat.utils import create_room, send_notice_to_room, send_super_message, send_room_to_users, send_message_to_user
from chat.models import Room, Message
from chat.serializers import MessageSerializer

# Create your views here.
class InvoiceView(mixins.ListModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get(self, request, *args, **kwargs):
        page = int(request.GET.get('page', "1"))
        cur_request = request.query_params.get("query", "")

        # user type
        query_set = Invoice.objects.exclude(invoice_type = "ADMIN")

        # query
        if cur_request != "":
            try:
                query_obj = json.loads(cur_request)
            except:
                return Response({"total": 0, "results": []}, status=status.HTTP_200_OK)

            # location
            location_val = query_obj.get("location_id", 0)
            if location_val > 0:
                query_set = query_set.filter(Q(order__parent_location__id = location_val) | Q(gift__location__id = location_val))

            # invoice type
            invoice_type = query_obj.get("invoice_type", "")
            if invoice_type != "":
                query_set = query_set.filter(invoice_type = invoice_type)

            # point_user_id
            point_user_id = query_obj.get("point_user_id", 0)
            point_receiver_id = query_obj.get("point_receiver_id", 0)

            if point_user_id and point_user_id > 0:
                query_set = query_set.filter(giver_id = point_user_id)
            else:
                if point_receiver_id and point_receiver_id > 0:
                    query_set = query_set.filter(taker_id = point_receiver_id)

                        # transfer from
            date_from = query_obj.get("from", "")
            if date_from != "":
                query_set = query_set.filter(
                    created_at__gte = get_edge_time(date_from, "from"))

            # transfer to
            date_to = query_obj.get("to", "")
            if date_to != "":
                query_set = query_set.filter(
                    created_at__lt = get_edge_time(date_to, "to"))

        total = query_set.count()
        paginator = Paginator(query_set.order_by('-created_at'), 10)
        invoices = paginator.page(page)

        return Response({"total": total, "results": InvoiceSerializer(invoices, many=True).data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data)
        if serializer.is_valid():
            try:
                new_invoice = serializer.save()
                return Response(InvoiceSerializer(new_invoice).data)
            except ValidationError:
                return Response(status = status.HTTP_406_NOT_ACCEPTABLE)            
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)

class InvoiceDetailView(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer
    queryset = Invoice.objects.all()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class UserInvoiceView(mixins.ListModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get(self, request, *args, **kwargs):
        page = int(request.GET.get('page', "1"))

        # user type
        query_set = Invoice.objects.filter(Q(giver = request.user) | Q(taker = request.user))
        total = query_set.count()
        paginator = Paginator(query_set.order_by('-created_at'), 10)
        try:
            invoices = paginator.page(page)
            return Response(data=InvoiceSerializer(invoices, many=True).data, status=status.HTTP_200_OK)
        except EmptyPage:
            return Response(data=[], status=status.HTTP_200_OK)

class DetailInvoiceView(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAdminPermission]
    serializer_class = InvoiceDetailSerializer

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

@api_view(['GET'])
@permission_classes([IsSuperuserPermission])
def get_invoice_total(request):
    buy_point = Invoice.objects.exclude(invoice_type = "ADMIN").filter(
        Q(invoice_type = 'BUY') | Q(invoice_type = 'CHARGE') | Q(invoice_type = 'AURO CHARGE')
    ).aggregate(Sum('take_amount'))['take_amount__sum']
    normal_invoices = Invoice.objects.exclude(invoice_type = 'ADMIN').exclude(invoice_type = 'CHARGE').exclude(invoice_type = 'BUY').exclude(invoice_type = 'AUTO_CHARGE')
    use_point = normal_invoices.aggregate(Sum('give_amount'))['give_amount__sum']
    pay_point = normal_invoices.aggregate(Sum('take_amount'))['take_amount__sum']

    if buy_point == None:
        buy_point = 0

    if use_point == None:
        use_point = 0

    if pay_point == None:
        pay_point = 0

    profit_point = use_point - pay_point    

    return Response({
        "buy": buy_point, "use": use_point, "pay": pay_point, "profit": profit_point
    }, status = status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAdminPermission])
def get_rank_users(request):
    user_type = request.GET.get('type', 'guest')
    page = int(request.GET.get('page', "1"))
    cur_query = request.query_params.get("query", "")
    size = int(request.GET.get('size', "100"))

    # user type
    query_set = Member.objects
    if user_type == "guest":
        query_set = query_set.filter(role = 1, is_active = True)
    else:
        query_set = query_set.filter(role = 0, is_active = True)

    # query
    date_from = ""
    date_to = ""
    if cur_query != "":
        try:
            query_obj = json.loads(cur_query)
        except:
            return Response({"total": 0, "results": []}, status=status.HTTP_200_OK)

        # location
        location_val = query_obj.get("location_id", 0)
        if location_val > 0:
            query_set = query_set.filter(location_id = location_val)

        date_from = query_obj.get("from", "")
        date_to = query_obj.get("to", "")
        
    time_filter = Q()

    if user_type == "guest":
        if date_from != "":
            time_filter &= Q(gave__created_at__gte = get_edge_time(date_from, "from"))
        if date_to != "":
            time_filter &= Q(gave__created_at__lt = get_edge_time(date_to, "to"))
        
        query_set = query_set.annotate(
            overall_points = Sum('gave__give_amount', filter=time_filter)
        ).order_by('-overall_points', '-call_times')
    else:        
        if date_from != "":
            time_filter &= Q(took__created_at__gte = get_edge_time(date_from, "from"))
        if date_to != "":
            time_filter &= Q(took__created_at__lt = get_edge_time(date_to, "to"))
        
        query_set = query_set.annotate(
            overall_points = Sum('took__take_amount', filter=time_filter)
        ).order_by('-overall_points', '-call_times')
    
    total = query_set.count()
    paginator = Paginator(query_set, size)
    rank_users = paginator.page(page)

    points_values = list(query_set.values_list('overall_points', flat = True).distinct())

    return Response({"total": total, "results": RankUserSerializer(
        rank_users, many=True, context = { 
            'from': parse(date_from).strftime("%Y-%m-%d") if date_from != "" else "", 
            'to': parse(date_to).strftime("%Y-%m-%d") if date_to != "" else "" }
    ).data, "values": points_values }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ranking(request):
    from dateutil.relativedelta import relativedelta

    user_type = request.GET.get('isCast', 'false')
    is_gift = request.GET.get('isGift', 'false')
    range = int(request.GET.get('range', '3'))

    # user type
    query_set = Member.objects.filter(setting__ranking_display = True)
    if user_type == "false":
        query_set = query_set.filter(role = 1, is_active = True)
    else:
        query_set = query_set.filter(role = 0, is_active = True)
        if is_gift == "false":
            query_set = query_set.filter(is_present = True)            

    # query       
    time_filter = Q()

    start_time = None
    end_time = None
    today = datetime.now().astimezone(pytz.timezone("Asia/Tokyo"))

    if range == 0:
        start_time = today.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        end_time = start_time + timedelta(days = 1)
    elif range == 1:
        week_day = (today.weekday() + 1) % 7
        start_time = today.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        start_time = start_time - timedelta(days = week_day)
        end_time = start_time + timedelta(days = 7)
    elif range == 2:
        start_time = today.replace(day = 1, hour = 0, minute = 0, second = 0, microsecond = 0)
        end_time = start_time + relativedelta(months = 1)
    else:
        start_time = today.replace(month = 1, day = 1, hour = 0, minute = 0, second = 0, microsecond = 0)
        end_time = start_time + relativedelta(years = 1)

    start_time.astimezone(pytz.timezone("UTC"))
    end_time.astimezone(pytz.timezone("UTC"))

    if user_type == "false":
        time_filter = Q(gave__created_at__gte = start_time) & Q(gave__created_at__lt = end_time)

        if is_gift == "true":
            time_filter &= Q(gave__invoice_type = "GIFT")
            query_set = query_set.annotate(
                overall_points = Sum('gave__give_amount', filter=time_filter)
            ).order_by('-overall_points', '-call_times')
        else:
            time_filter &= Q(gave__invoice_type = "CALL")
            query_set = query_set.annotate(
                overall_points = Sum('gave__give_amount', filter=time_filter)
            ).order_by('-overall_points', '-call_times')
    else:        
        time_filter = Q(took__created_at__gte = start_time) & Q(took__created_at__lt = end_time)

        if is_gift == "true":
            time_filter &= Q(took__invoice_type = "GIFT")
            query_set = query_set.annotate(
                overall_points = Sum('took__take_amount', filter=time_filter)
            ).order_by('-overall_points', '-call_times')
        else:
            time_filter &= Q(took__invoice_type = "CALL")
            query_set = query_set.annotate(
                overall_points = Sum('took__take_amount', filter=time_filter)
            ).order_by('-overall_points', '-call_times')
    
    return Response(MainInfoSerializer(query_set[:10], many = True).data)

@api_view(['POST'])
@permission_classes([IsAdminPermission])
def create_order(request):
    serializer = AdminOrderCreateSerializer(data = request.data)

    if serializer.is_valid():
        input_data = serializer.validated_data
        order_data = input_data.get('order')
        notify_cast = input_data.get('notify_cast')
        notify_guest = input_data.get('notify_guest')

        order_data.pop('situation_ids')

        # check guest
        guest_id = order_data.get('user_id', 0)
        try:
            guest = Member.objects.get(pk = guest_id)
            if guest.role != 1:
                return Response(status = status.HTTP_406_NOT_ACCEPTABLE)    
        except Member.DoesNotExist:
            return Response(status = status.HTTP_406_NOT_ACCEPTABLE)
        
        order = Order.objects.create(**order_data)
        
        # notification
        message_content = "管理者によりオーダーが作られました。\n 確認お願いいたします。"
        if notify_cast > 0:
            cast_ids = []
            if notify_cast == 1:
                cast_ids = list(Member.objects.filter(role = 0, location = order.parent_location).values_list('id', flat = True))
            else:
                cast_ids = list(Member.objects.filter(role = 0, is_present = True).values_list('id', flat = True))
            for cast_id in cast_ids:
                send_super_message("system", cast_id, message_content)
        
        if notify_guest > 0:
            send_super_message("system", order.user_id, message_content)

        today_date = datetime.now().astimezone(pytz.timezone("Asia/Tokyo")).date()
        meet_date = order.meet_time_iso.astimezone(pytz.timezone("Asia/Tokyo")).date()
        
        # send order create
        cast_ids = list(Member.objects.filter(role = 0, location = order.parent_location).values_list('id', flat = True))
        send_call(order, cast_ids, "create")
        
        # call type send 
        if meet_date == today_date:
            send_call_type("today", cast_ids)
        if meet_date > today_date:
            send_call_type("tomorrow", cast_ids)
            
        return Response(OrderSerializer(order).data, status = status.HTTP_200_OK)
    else:
        print(serializer.errors)
        return Response(status = status.HTTP_400_BAD_REQUEST)

class OrderView(generics.GenericAPIView):
    permission_classes = ( IsGuestPermission | IsSuperuserPermission, )
    serializer_class = OrderSerializer

    def get(self, request):
        import json

        page = int(request.GET.get('page', "1"))
        size = int(request.GET.get('size', "10"))

        cur_request = request.query_params.get("query", "")
        query_set = Order.objects

        if cur_request != "":
            try:
                query_obj = json.loads(cur_request)
            except:
                return Response({"total": 0, "results": []}, status=status.HTTP_200_OK)

            location_id = query_obj.get('location_id', 0)
            area_id = query_obj.get('area_id', 0)
            status_val = query_obj.get('status', -1)
            cost_plan_id = query_obj.get('cost_plan_id', 0)
            guest_id = query_obj.get('guest_id', 0)
            ids_array = query_obj.get('ids_array', [])

            if len(ids_array) > 0:
                query_set = query_set.filter(id__in = ids_array)

            if location_id > 0:
                query_set = query_set.filter(parent_location_id = location_id)
                
            if area_id > 0:
                query_set = query_set.filter(location_id = area_id)

            if status_val > -1:
                if status_val != 3:
                    query_set = query_set.filter(status = status_val)
                else:
                    query_set = query_set.filter(Q(status = 3) | Q(status = 4))
            
            if location_id > 0:
                query_set = query_set.filter(cost_plan_id = cost_plan_id)
            
            if guest_id != None:
                if guest_id > 0:                
                    query_set = query_set.filter(user_id = guest_id)

        # sort order
        sort_field = request.GET.get("sortField", "")
        sort_order = request.GET.get("sortOrder", "")
        if sort_field != "null" and sort_field != "":
            if sort_order == "ascend":
                query_set = query_set.order_by(sort_field)
            else:
                query_set = query_set.order_by("-{}".format(sort_field))
        else:
            query_set = query_set.order_by("-created_at")

        total = query_set.count()
        paginator = Paginator(query_set, size)
        orders = paginator.page(page)

        return Response({"total": total, "results": OrderSerializer(orders, many=True).data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.get_serializer(data = request.data)
        if serializer.is_valid():
            new_order = serializer.save()
            new_order.user = request.user
            new_order.save()

            # send system message       
            location_str = new_order.location.name if new_order.location != None else new_order.location_other
            start_time_str = new_order.meet_time_iso.astimezone(pytz.timezone("Asia/Tokyo")).strftime("%Y{0}%m{1}%d{2}%H{3}%M{4}").format(*"年月日時分")
            end_time_str = new_order.ended_predict.astimezone(pytz.timezone("Asia/Tokyo")).strftime("%Y{0}%m{1}%d{2}%H{3}%M{4}").format(*"年月日時分")
            message_content = "ご予約のリクエストありがとうございます。\n \
                現在合流可能なキャストをお探ししています。 \n \
                尚リクエスト確定後のキャンセルはお受けできません。予めご了承ください。 \n \
                場所 : {0} \n \
                時間 : {1} ~ {2} \n \
                人数 : {3}人".format(location_str, start_time_str, end_time_str, new_order.person)
            
            today_date = datetime.now().astimezone(pytz.timezone("Asia/Tokyo")).date()
            meet_date = new_order.meet_time_iso.astimezone(pytz.timezone("Asia/Tokyo")).date()
            
            # call send
            cast_ids = list(Member.objects.filter(location = new_order.parent_location).values_list('id', flat = True).distinct())
            send_call(new_order, cast_ids, "create")

            # call type send 
            if meet_date == today_date:
                send_call_type("today", cast_ids)
            if meet_date > today_date:
                send_call_type("tomorrow", cast_ids)

            send_super_message("system", request.user.id, message_content)
            return Response(OrderSerializer(new_order).data, status = status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(status = status.HTTP_400_BAD_REQUEST)

class OrderDetailView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    permission_classes = (IsGuestPermission | IsSuperuserPermission, )
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        cur_order = self.get_object()
        old_status = cur_order.status

        if cur_order.is_private:
            for key_item in ["cost_plan_id", "situations"]:
                if key_item in request.data.keys():
                    request.data.pop(key_item)

        serializer = self.get_serializer(cur_order, data = request.data)
        if serializer.is_valid():
            new_order = serializer.save()

            # call status changed handler
            if old_status != new_order.status:
                if new_order.status >= 5:
                    for ongoingJoin in new_order.joins.filter(is_started = True, is_ended = False, status = 1):
                        ongoingJoin.is_ended = True
                        ongoingJoin.ended_at = timezone.now()
                        ongoingJoin.save()

                        message = "{}の合流は終了されました。".format(ongoingJoin.user.nickname)
                        send_notice_to_room(new_order.room, message, True)
                    
                    if new_order.room != None:                       

                        # send room event
                        send_room_event("update", new_order.room)

            return Response(OrderSerializer(new_order).data)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAdminPermission])
def cancel_order(request, id):
    cur_admin = request.user
    cur_order = Order.objects.get(pk = id)
    if not cur_admin.is_superuser and cur_admin.location_id != cur_order.parent_location_id:
        return Response(status = status.HTTP_403_FORBIDDEN)
    else:
        if cur_order.status != 9:
            cur_order.status = 9
            cur_order.save()

        # end join
        for ongoingJoin in cur_order.joins.filter(status = 1, is_started = True, is_ended = False):
            ongoingJoin.is_ended = True
            ongoingJoin.ended_at = timezone.now()
            ongoingJoin.save()

        # update room and send event
        message = "管理画面よりオーダーがキャンセルされました。\n お問い合わせは運営局へご連絡ください。"
        if cur_order.room != None:
            # if cur_order.room.is_group:
            #     cur_order.room.status = 3
            # else:
            #     cur_order.room.status = 0            
            cur_order.room.last_message = message
            cur_order.room.save()
            send_notice_to_room(cur_order.room, message, False)

            # send room event
            send_room_event("ended", cur_order.room)
        else:
            send_super_message("system", cur_order.user.id, message)

        cast_ids = list(Member.objects.filter(location = cur_order.parent_location).values_list('id', flat = True))
        send_call(cur_order, cast_ids, "delete")
        
        join_ids = list(cur_order.joins.values_list('user_id', flat = True))
        send_call(cur_order, join_ids, "mine")

        return Response(OrderSerializer(cur_order).data, status = status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAdminPermission])
def get_order_counts(request):
    is_normal = int(request.GET.get('is_normal', '1'))
    status_array = []
    if is_normal == 1:
        status_title = [
            'Collecting customers', 'Selecting Cast Name',
            'Cast Confirmed', 'Meeting Finished', 'Pay Finished', 'Cancel with not enough casts'
        ]
        status_numbers = [0, 1, 3, 5, 7, 8]
        for index, status_number in enumerate(status_numbers):
            if status_number != 3:
                orders_count = Order.objects.filter(status = status_number).count()
            else:
                orders_count = Order.objects.filter(Q(status = 3) | Q(status = 4)).count()
            status_array.append({
                "title": status_title[index],
                "count": orders_count,
                "value": status_number,
                "ids_array": []
            })
    else:
        status_title = [
            'Collecting Cast + Not Enough', 'Cast Confirm + Start Time Exceeds',
            'Extended time exceeds 8 hours', 'Payment failed'
        ]

        # collecting cast not enough
        query_set = Order.objects.annotate(joined_count = Count('joins')).filter(status = 0, joined_count__lt = F('person'))
        orders_count = query_set.count()
        ids_array = list(query_set.values_list('id', flat = True).distinct())

        status_array.append({
            "title": "Collecting Cast + Not Enough",
            "count": orders_count,
            "ids_array": ids_array,
            "value": 0
        })

        # cast confirm + start time exceeds
        query_set = Order.objects.filter(status = 3, ended_predict__lt = timezone.now())
        orders_count = query_set.count()
        ids_array = list(query_set.values_list('id', flat = True).distinct())
        
        status_array.append({
            "title": "Cast Confirm + Start Time Exceeds",
            "count": orders_count,
            "ids_array": ids_array,
            "value": 0
        })

        # extended time exceeds
        ended_predict_time = timezone.now() - timedelta(hours = 8)
        query_set = Order.objects.filter(status = 4, ended_predict__lt = ended_predict_time)
        orders_count = query_set.count()
        ids_array = list(query_set.values_list('id', flat = True).distinct())
        
        status_array.append({
            "title": "Extened time exceeds 8 hours",
            "count": orders_count,
            "ids_array": ids_array,
            "value": 0
        })

        # payment failed
        query_set = Order.objects.filter(status = 10)
        orders_count = query_set.count()
        ids_array = list(query_set.values_list('id', flat = True).distinct())
        
        status_array.append({
            "title": "Payment failed",
            "count": orders_count,
            "ids_array": ids_array,
            "value": 0
        })
                
    return Response(status_array)

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

@api_view(['GET'])
@permission_classes([IsSuperuserPermission])
def get_month_data(request):
    end_date = timezone.now().date()
    start_date = datetime.strptime(end_date.strftime("%Y-%m-01"), "%Y-%m-%d").date()
    result_data = []
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"]
    sum_data = {
        "date_str": "合計",
        "order_counts": 0,
        "order_points": 0,
        "gift_points": 0,
        "gift_counts": 0,
        "buy_points": 0
    }

    for single_date in daterange(start_date, end_date):
        temp_data = {}

        # get invoice data of current date
        temp_data["date_str"] = "{0}({1})".format(single_date.strftime("%Y-%m-%d"), weekday_str[single_date.weekday()])
        temp_data["order_counts"] = Order.objects.filter(created_at__date = single_date).count()
        sum_data["order_counts"] += temp_data["order_counts"]

        temp_data["order_points"] = Invoice.objects.filter(
            created_at__date = single_date, invoice_type = "CALL"
            ).aggregate(Sum('give_amount'))['give_amount__sum']
        if temp_data["order_points"] != None:
            sum_data["order_points"] += temp_data["order_points"]

        temp_data['gift_counts'] = Invoice.objects.filter(created_at__date = single_date, invoice_type = "GIFT").count()
        sum_data['gift_counts'] += temp_data['gift_counts']
    
        temp_data['gift_points'] = Invoice.objects.filter(
            created_at__date = single_date, invoice_type = "GIFT"
            ).aggregate(Sum('give_amount'))['give_amount__sum']
        if temp_data['gift_points'] != None:
            sum_data['gift_points'] += temp_data['gift_points']

        temp_data['buy_points'] = Invoice.objects.filter(
            created_at__date = single_date, invoice_type = "BUY"
            ).aggregate(Sum('take_amount'))['take_amount__sum']
        if temp_data['buy_points'] != None:
            sum_data['buy_points'] += temp_data['buy_points']
        

        result_data.append(temp_data)

    result_data.append(sum_data)
    return Response(result_data)

class JoinView(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAdminPermission]
    serializer_class = JoinSerializer
    queryset = Join.objects.all()

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, pk, *args, **kwargs):
        cur_obj = Join.objects.get(pk = pk)
        ex_started_at = cur_obj.started_at 
        ex_ended_at = cur_obj.ended_at
        ex_started = cur_obj.is_started
        ex_ended = cur_obj.is_ended

        serializer = self.get_serializer(cur_obj, data = request.data)

        if serializer.is_valid():
            new_obj = serializer.save()
            if new_obj.order.room != None:
                cur_room = new_obj.order.room
                if ex_started_at == None and new_obj.started_at != None:
                    message = "{0}は合流しました。".format(new_obj.user.nickname)
                    new_obj.is_started = True
                    new_obj.save()
                    send_notice_to_room(cur_room, message)
                if ex_started_at != None and new_obj.started_at == None:
                    message = "{0}の合流は管理者によりキャンセルされました。".format(new_obj.user.nickname)
                    new_obj.is_started = False
                    new_obj.save()
                    send_notice_to_room(cur_room, message)                    
                if ex_ended_at == None and new_obj.ended_at != None:
                    message = "{0}は解散しました。".format(new_obj.user.nickname)
                    new_obj.is_ended = True
                    new_obj.save()
                    send_notice_to_room(cur_room, message)
                if ex_ended_at != None and new_obj.ended_at == None:
                    message = "{0}の解散は管理者によりキャンセルされました。".format(new_obj.user.nickname)
                    new_obj.is_ended = False
                    new_obj.save()
                    send_notice_to_room(cur_room, message)
                
                # order state update
                cur_order = Order.objects.get(pk = new_obj.order_id)
                if not ex_ended and new_obj.is_ended:
                    if cur_order.joins.filter(is_ended = False).count() == 0 and cur_order.status < 5:
                        cur_order.status = 5
                        cur_order.save()
                        message = "管理者より合流が完了しました。"
                elif ex_ended and not new_obj.is_ended:
                    if cur_order.status == 5:
                        if new_obj.is_started:
                            cur_order.status = 4
                        else:
                            if cur_order.joins.filter(is_started = True).count() > 0:
                                cur_order.status = 4
                            else:
                                cur_order.status = 3
                        cur_order.save()
                elif not ex_ended and not new_obj.is_ended:
                    if not ex_started and new_obj.is_started:
                        if cur_order.status == 3:
                            cur_order.status = 4
                    if ex_started and not new_obj.is_started:
                        if cur_order.joins.filter(is_started = True).count() == 0:
                            cur_order.status = 3
                        else:
                            cur_order.status = 4
                    cur_order.save()
                    
                send_room_event("update", cur_room)
            return Response(JoinSerializer(new_obj).data)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminPermission])
def drop_join(request, id):
    try:
        join = Join.objects.get(pk = id)
        join.dropped = True
        join.save()
        return Response(status = status.HTTP_200_OK)
    except Join.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAdminPermission])
def recover_join(request, id):
    try:
        join = Join.objects.get(pk = id)
        join.dropped = False
        join.save()
        return Response(status = status.HTTP_200_OK)
    except Join.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

class OrderCastView(generics.GenericAPIView):
    permission_classes = [IsCastPermission]
    serializer_class = OrderSerializer

    def get(self, request):
        cur_user = request.user
        mode = request.GET.get('mode', 'today')
        page = int(request.GET.get('page', "1"))

        query_set = Order.objects.filter(parent_location = cur_user.location, is_private = False)

        today_date = datetime.now(pytz.timezone("Asia/Tokyo"))
        today_date = today_date.replace(hour = 0, minute = 0, second = 0, microsecond = 0)

        tomorrow_date = today_date + timedelta(days = 1)
        if mode == 'today':
            query_set = query_set.filter(status__lt = 3, meet_time_iso__gte = today_date, meet_time_iso__lt = tomorrow_date)
        elif mode == 'tomorrow':
            query_set = query_set.filter(status__lt = 3, meet_time_iso__gte = tomorrow_date)
        else:
            query_set = query_set.filter(status__lte = 6).filter(joins__user = cur_user)

        query_set = query_set.order_by('-created_at')
        paginator = Paginator(query_set, 5)
        orders = paginator.page(page)

        return Response(OrderSerializer(orders, many=True).data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsCastPermission])
def apply_order(request, id):
    try:
        cur_order = Order.objects.get(pk = id)

        # order validation
        if cur_order.is_private or cur_order.status >= 2:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        

        new_join = Join.objects.create(user = request.user, order = cur_order)
        joins_num = cur_order.joins.count()
        if joins_num == cur_order.person and cur_order.status == 0:
            cur_order.status = 1
            cur_order.save()

            collect_end = cur_order.collect_ended_at.astimezone(pytz.timezone("Asia/Tokyo"))
            
            # send message to guest
            cur_message = "おめでとうございます♪\n \
                キャストが集まり、オーダーのリクエストが確定されました。\n \
                <a href='/main/call/desire/{0}'>こちら</a>よりお好みのキャストの選択ができます♪\n \
                ＊このオーダーは現在募集中なので、より多くのキャストが集まる可能性がございます。\n \
                ＊お好みのキャスト{2}名を選択するか{1}を過ぎると自動でマッチングが開始されチャットルームが作成されます。\n \
                <a class='gui-message-btn' href='/main/call/desire/{0}'>キャスト選択画面へ</a> \
                ".format(cur_order.id, collect_end.strftime("%Y{0}%m{1}%d{2}%H{3}%M{4}").format(*"年月日時分"), cur_order.person)

            send_super_message("system", cur_order.user.id, cur_message)

        # inform guest of new cast application
        if joins_num > cur_order.person:
            send_applier(cur_order.id, 0, cur_order.user.id)

        # inform applier to casts
        cur_order = Order.objects.get(pk = id)

        cast_ids = list(Member.objects.filter(location = cur_order.parent_location).values_list('id', flat = True).distinct())
        send_call(cur_order, cast_ids, "update")

        return Response(JoinSerializer(new_join).data)

    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsCastPermission])
def check_order(request, id):
    try:
        cur_order = Order.objects.get(pk = id)
        cast = request.user

        started_time = cur_order.meet_time_iso
        end_time = cur_order.meet_time_iso + timedelta(hours = cur_order.period)

        candidate_ranges = []

        # get current join data
        for joinItem in cast.joins.filter(is_ended = False):
            if joinItem.is_started:

                candidate_item = {
                    "started_at": joinItem.started_at,
                    "ended_at": joinItem.started_at + timedelta(hours = joinItem.order.period),
                    "allowed": False,
                    "id": joinItem.order.id
                }

            else:
                candidate_item = {
                    "started_at": joinItem.order.meet_time_iso,
                    "ended_at": joinItem.order.meet_time_iso + timedelta(hours = joinItem.order.period),
                    "allowed": False,
                    "id": joinItem.order.id
                }
                if joinItem.order.status == 0:
                    candidate_item["allowed"] = True

            candidate_ranges.append(candidate_item)
        
        # check join data
        cur_orders = []
        for range_item in candidate_ranges:

            # two ranges intersected
            if range_item['ended_at'] > started_time and range_item['started_at'] < end_time:
                if range_item['allowed']:
                    cur_orders.append(OrderSerializer(Order.objects.get(pk = range_item['id'])).data)
                else:
                    return Response({
                        "result": False, "data": [OrderSerializer(Order.objects.get(pk = range_item['id'])).data]
                    })
        return Response({
            "result": True, "data": cur_orders
        })

    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsCastPermission])
def cancel_order_apply(request):
    cancel_ids = request.GET.get('ids').split(",")
    for orderIdStr in cancel_ids:
        orderId = int(orderIdStr)
        try:
            cur_order = Order.objects.get(pk = orderId)
            cur_join = cur_order.joins.filter(user = request.user).get()
            if cur_order != None:
                if cur_order.status == 0:
                    cur_join.delete()

                    # notify to cast
                    cast_ids = list(Member.objects.filter(location = cur_order.parent_location).values_list('id', flat = True).distinct())
                    send_call(cur_order, cast_ids, "update")
                else:
                    return Response(status = status.HTTP_406_NOT_ACCEPTABLE)
        except Join.DoesNotExist:
            continue        

    return Response(status = status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_cast_status(request, id):
    try:
        start_time = parse(request.GET.get("start", ""))
        end_time = parse(request.GET.get("end", ""))
        print(start_time)
        print(start_time.tzinfo is None or start_time.tzinfo.utcoffset(start_time) is None)
        print(end_time)
        try:
            room = Room.objects.get(pk = id)
            if room.is_group:
                return Response(status = status.HTTP_400_BAD_REQUEST)
            
            cast = request.user
            if request.user.role == 1:
                for user in room.users.all():
                    if user.role == 0:
                        cast = user
            
            for joinItem in cast.joins.filter(is_ended = False):
                if joinItem.is_started:
                    if joinItem.started_at < end_time and (joinItem.started_at + timedelta(hours = joinItem.order.period)) > start_time:
                        return Response(False)
                else:
                    if joinItem.order.meet_time_iso < end_time and joinItem.order.meet_time_iso + timedelta(hours = joinItem.order.period) > start_time:
                        return Response(False)       

            return Response(True)
            
        except Room.DoesNotExist:
            return Response(status = status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsGuestPermission])
def confirm_cast(request, id, user_id):
    guest = request.user
    try:
        cur_order = Order.objects.get(pk = id)

        # check if user is call's guest
        if cur_order.user.id != guest.id:
            return Response(status = status.HTTP_406_NOT_ACCEPTABLE)

        # if it has already been confirmed
        if cur_order.status >= 3:
            return Response(status = status.HTTP_403_FORBIDDEN)      
        
        # else
        cur_user = Member.objects.get(pk = user_id)

        if cur_order.joins.filter(user__id = cur_user.id).count() == 0:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        else:
            cur_order.joins.filter(user__id = cur_user.id).update(status = 1, selection = 1)
            room_created = False
            room_id = 0

            # if confirmed person fills
            if cur_order.joins.filter(status = 1, selection = 1).count() == cur_order.person:
                cast_ids = list(cur_order.joins.filter(status = 1, selection = 1).values_list('user_id', flat = True))
                room_created = True
                room_id = create_room(cur_order, cast_ids)

            # send system message to rejected casts
            remove_cast_ids = list(cur_order.joins.exclude(status = 1, selection = 1).values_list('user_id', flat = True))
            start_time_str = cur_order.meet_time_iso.astimezone(pytz.timezone("Asia/Tokyo")).strftime("%Y{0}%m{1}%d{2}%H{3}%M{4}").format(*"年月日時分")
            message = "オーダーにエントリー頂き、誠にありが \
                とうございました。 残念ながら「合流: {0} {1} キャスト{2}人」のマッチングでは外れました。\
                是非またオーダーにエントリー頂けます。ようお願いいたします!".format(
                    cur_order.location.name if cur_order.location else cur_order.location_other, start_time_str, cur_order.person)
            for cast_id in remove_cast_ids:
                send_super_message("system", cast_id, message)

            # send confirm to cast
            send_call(cur_order, [cur_user.id], "confirm")

            return Response({ "created": room_created, "room": room_id }, status = status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAdminPermission])
def make_room(request, id):
    cur_admin = request.user
    cur_order = Order.objects.get(pk = id)
    if cur_admin.location_id != cur_order.parent_location_id:
        return Response(status = status.HTTP_403_FORBIDDEN)
    else:
        cast_ids = list(cur_order.joins.filter(dropped = False).values_list('user_id', flat = True))

        # remove room if exists
        old_cast_ids = []
        if cur_order.room != None:
            old_cast_ids = list(cur_order.room.users.filter(role = 0).values_list('id', flat = True))
            room_title = cur_order.room.title

            # cur_order.room.delete()
            message = "残念ですが管理画面よりチャットルーム「{0}」から却下されました。\
                是非またオーダーにエントリー頂けますようお願いいたします!".format(room_title)

            # old cast ids
            kicked_users = []
            for cast_id in old_cast_ids:
                if not cast_id in cast_ids:
                    kicked_users.append(cast_id)
                    send_super_message("system", cast_id, message)

            # send room delete
            send_room_to_users(cur_order.room, kicked_users, "delete")
            
            # room users change
            room_users = [cur_order.user.id] + cast_ids
            cur_order.room.users.clear()
            cur_order.room.users.set(room_users)

            # added users
            add_users = []
            for cast_id in cast_ids:
                if not cast_id in old_cast_ids:
                    add_users.append(cast_id)
            send_room_to_users(cur_order.room, add_users, "create")

            # remove dropped casts
            cur_order.joins.filter(dropped = True).delete()
            cur_order.joins.update(status = True)
            cur_order.person = cur_order.joins.count()            

        else:            
            # remove dropped casts
            cur_order.joins.filter(dropped = True).delete()
            cur_order.joins.update(status = True)
            cur_order.person = cur_order.joins.count()
            create_room(cur_order, cast_ids)

        return Response(OrderSerializer(Order.objects.get(pk = cur_order.id)).data, status = status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsGuestPermission])
def auto_match(request, id):
    guest = request.user
    try:
        cur_order = Order.objects.get(pk = id)

        # check if user is call's guest
        if cur_order.user.id != guest.id:
            return Response(status = status.HTTP_406_NOT_ACCEPTABLE)
        
        # if it has already been confirmed
        if cur_order.status != 1:
            return Response(status = status.HTTP_403_FORBIDDEN)
        
        persons = cur_order.person

        if cur_order.joins.filter(status = 1).count() < persons:
                
            # if remaining casts are less than required
            if cur_order.joins.filter(status = 0, dropped = False).count() < persons - cur_order.joins.filter(status = 1).count():
                return Response(status = status.HTTP_406_NOT_ACCEPTABLE)

            # order remaining casts by call times
            candidates = list(cur_order.joins.filter(status = 0, dropped = False).order_by('user__call_times').values_list('id', flat = True))
            added_cast_ids = []
            for _ in range(persons - cur_order.joins.filter(status = 1).count()):
                candidate_id = candidates.pop(0)
                added_cast_ids.append(candidate_id)
                cur_join = Join.objects.get(pk = candidate_id)
                cur_join.status = 1
                cur_join.selection = 0
                cur_join.save()
            
            # send cast ids call
            send_call(cur_order, added_cast_ids, "create")

            # remove other joins
            remove_cast_ids = list(cur_order.joins.filter(status = 0).values_list('user_id', flat = True))
            start_time_str = cur_order.meet_time_iso.astimezone(pytz.timezone("Asia/Tokyo")).strftime("%Y{0}%m{1}%d{2}%H{3}%M{4}").format(*"年月日時分")
            message = "オーダーにエントリー頂き、誠にありが \
                とうございました。 残念ながら「合流: {0} {1} キャスト{2}人」のマッチングでは外れました。\
                是非またオーダーにエントリー頂けますようお願いいたします!".format(
                    cur_order.location.name if cur_order.location else cur_order.location_other, start_time_str, cur_order.person)
            for cast_id in remove_cast_ids:
                send_super_message("system", cast_id, message)

            cur_order.joins.filter(status = 0).delete()

            # make room for confirmed join casts
            room_id = create_room(cur_order, list(cur_order.joins.values_list('user_id', flat = True)))

            # notify guest
            send_applier(cur_order.id, room_id, cur_order.user_id)

            return Response(RoomSerializer(Room.objects.get(pk = room_id)).data, status = status.HTTP_200_OK)
        
        else:
            return Response(status = status.HTTP_406_NOT_ACCEPTABLE)

    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsCastPermission])
def check_meet_time(request, id):
    try:
        room = Room.objects.get(pk = id)
        if room.users.filter(id = request.user.id).count() > 0:
            cur_order = room.orders.filter(is_private = not room.is_group).filter(Q(status = 4) | Q(status = 3)).order_by(
                '-status', 'meet_time_iso').first()
            if cur_order != None:
                return Response(cur_order.ended_predict < timezone.now())
            else:
                return Response(False)
        return Response(status = status.HTTP_400_BAD_REQUEST)
    except Room.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsCastPermission])
def get_room_joins(request, id):
    try:
        room = Room.objects.get(pk = id)
        if room.users.filter(id = request.user.id).count() > 0:            
            cur_order = room.orders.filter(is_private = not room.is_group).filter(Q(status = 4) | Q(status = 3)).order_by(
                '-status', 'meet_time_iso').first()
            if cur_order != None:
                if cur_order.joins.filter(status = 1, user = request.user).count() > 0:
                    cur_join = cur_order.joins.filter(status = 1, user = request.user).first()
                    return Response({"result": True, "data": JoinSerializer(cur_join).data})
            return Response({"result": False, "data": None})
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)
    except Room.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsGuestPermission])
def check_room_status(request, id):
    try:
        room = Room.objects.get(pk = id)
        if room.users.filter(id = request.user.id).count() > 0:
            cur_order = room.orders.filter(is_private = True).filter(Q(status = 4) | Q(status = 3)).order_by(
                '-status', 'meet_time_iso').first()
            
            return Response(cur_order == None, status = status.HTTP_200_OK)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)
    except Room.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsCastPermission])
def start_joins(request, id):
    try:
        room = Room.objects.get(pk = id)
        # if room.status == 2:
        if room.users.filter(id = request.user.id).count() > 0 and room.orders.count() > 0:
            cur_order = room.orders.order_by('-created_at').first()

            if cur_order.status != 3 and cur_order.status != 4:
                return Response(status = status.HTTP_406_NOT_ACCEPTABLE)

            if cur_order.joins.filter(status = 1, user = request.user).count() > 0:
                cur_join = cur_order.joins.filter(status = 1, user = request.user).first()
                cur_join.is_started = True
                cur_join.started_at = timezone.now()
                cur_join.save()

                # cast update call times
                cur_join.user.call_times += 1
                cur_join.user.save()

                if cur_order.status == 3:
                    cur_order.status = 4
                    cur_order.save()

                    # update guest call times, group times, private times
                    guest = cur_order.user
                    if cur_order.is_private:
                        guest = cur_order.user if cur_order.user.role == 1 else cur_order.target
                        guest.private_times += 1
                    else:
                        guest.group_times += 1
                    
                    guest.call_times += 1
                    guest.save()                    
                
                # send system message
                message = "{0}は合流しました。".format(request.user.nickname)
                room.last_message = message
                room.save()
                send_notice_to_room(room, message, True)

                return Response(JoinSerializer(cur_join).data)
        return Response(status = status.HTTP_400_BAD_REQUEST)
    except Room.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsCastPermission])
def end_joins(request, id):
    try:
        room = Room.objects.get(pk = id)
        if room.users.filter(id = request.user.id).count() > 0 and room.orders.count() > 0:
            cur_order = room.orders.order_by('-created_at').first()
            if cur_order.joins.filter(status = 1, user = request.user).count() > 0:
                cur_join = cur_order.joins.filter(status = 1, user = request.user).first()
                cur_join.is_ended = True
                cur_join.ended_at = timezone.now()
                cur_join.save()

                # send system message
                message = "{0}は解散しました。".format(request.user.nickname)
                room.last_message = message
                room.save()
                send_notice_to_room(room, message, True)

                # send review message to cast
                cast_message = "この度はオーダーへのご参加ありがとうございます。\n\
                    お客様のレビューにご協力お願いいたします。\n\
                    <a href = '/main/chat/review/{0}?room_id={1}'>レビュー画面へ</a>".format(cur_order.id, room.id)
                send_super_message("system", cur_join.user_id, cast_message)

                # if all finished
                if cur_order.joins.filter(is_ended = False).count() == 0:
                    message = "終了しました。"
                    room.last_message = message
                    # if room.is_group:
                    #     room.status = 3
                    # else:
                    #     room.status = 0
                    room.save()
                    send_notice_to_room(room, message, True)

                    # send room event
                    send_room_event("ended", room)

                    # send review message
                    guest = cur_order.user
                    if cur_order.is_private:
                        guest = cur_order.user if cur_order.user.role == 1 else cur_order.target
                    guest_message = "この度はご利用頂きありがとうございます！\n\
                        ご満足いただけましたでしょうか？\n\
                        Guiではサービス向上の一環として、ご利用いただいたお客様へ\n\
                        キャストの評価をお願いしております。\n\
                        もしよろしければ、今後のサービス向上のため\n\
                        お手すきの際に評価をいただけますでしょうか。\n\
                        <a href = '/main/chat/review/{0}?room_id={1}'>レビュー画面へ</a>".format(cur_order.id, room.id)
                    send_super_message("system", guest.id, guest_message)

                    # update order status
                    cur_order.status = 5
                    cur_order.save()

                return Response(JoinSerializer(cur_join).data)
        return Response(status = status.HTTP_400_BAD_REQUEST)
    except Room.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((IsCastPermission | IsGuestPermission, ))
def request_call(request):
    for key_item in ["cost_plan_id", "situations"]:
        if key_item in request.data.keys():
            request.data.pop(key_item)
        
    serializer = OrderSerializer(data = request.data)

    if serializer.is_valid():
        order = serializer.save()
        
        period_start_str = order.meet_time_iso.astimezone(pytz.timezone("Asia/Tokyo")).strftime(
            "%Y{0}%m{1}%d{2}%H{3}%M{4}").format(*"年月日時分")
        period_end_str = (order.meet_time_iso + timedelta(hours = order.period)).astimezone(pytz.timezone("Asia/Tokyo")).strftime(
            "%Y{0}%m{1}%d{2}%H{3}%M{4}").format(*"年月日時分")
        message = ""

        if request.user.role == 0:
            message = "個人オーダーのリクエストありがとうございます。\n\
                お客様からの返答をお待ちください。 \n \
                場所：{0}\n\
                時間：{1} ~ {2}\n\
                料金：{3:,d}P\n\
                <a href = '/main/chat/request/{4}?room_id={5}'>詳細はこちら</a>".format(
                    order.location.name, period_start_str, period_end_str, order.cost_value * 2 * order.period, order.id, order.room.id
                )
        else:
            message = "個人オーダーのリクエストありがとうございます。\n\
                キャストからの返答をお待ちください。\n\
                尚リクエスト確定後のキャンセルはお受けできません。予めご了承ください。\n\
                場所：{0}\n\
                時間：{1} ~ {2}\n\
                <a href = '/main/chat/request/{3}?room_id={4}'>詳細はこちら</a>".format(
                    order.location.name, period_start_str, period_end_str, order.id, order.room.id
                )
        
        self_message = Message.objects.create(content = message, room = order.room, 
            sender = request.user, receiver = request.user, is_read = True)

        order.room.last_message = message
        order.room.save()

        partner = order.room.users.exclude(id = request.user.id).first()

        order.user = request.user
        order.target = partner
        if order.user.role == 1:
            order.cost_value = partner.point_half
            order.cost_extended = order.cost_value * 1.3
        else:
            order.cost_extended = order.cost_value * 1.3

        order.save()

        target_message = Message.objects.create(content = message, room = order.room,
            sender = request.user, receiver = Member.objects.get(pk = partner.id), is_read = False, follower = self_message)
        
        send_message_to_user(target_message, partner.id)

        return Response(MessageSerializer(self_message).data)
    else:
        print(serializer.errors)
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order(request, pk):
    try:
        order = Order.objects.get(pk = pk)
        cur_user = request.user
        if order.user.id != cur_user.id and order.target.id != cur_user.id:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        else:
            return Response(OrderSerializer(order).data, status = status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cancel_request(request, pk):
    try:
        order = Order.objects.get(pk = pk)
        cur_user = request.user
        if order.user.id != cur_user.id:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        else:
            if order.is_cancelled or order.is_replied:
                return Response(status = status.HTTP_406_NOT_ACCEPTABLE)
            else:
                order.is_cancelled = True
                order.save()

                # send notification
                message = "{}はオーダー依頼をキャンセルしました。".format(cur_user.nickname)
                order.room.last_message = message
                order.room.save()
                send_notice_to_room(order.room, message, True)

                return Response(OrderSerializer(order).data, status = status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reject_request(request, pk):
    try:
        order = Order.objects.get(pk = pk)
        cur_user = request.user
        if order.user.id == cur_user.id:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        else:
            if order.is_cancelled or order.is_replied:
                return Response(status = status.HTTP_406_NOT_ACCEPTABLE)
            else:
                order.is_replied = True
                order.is_accepted = False
                order.save()

                # send notification
                message = "{}は合流拒否しました。".format(cur_user.nickname)
                order.room.last_message = message
                order.room.save()
                send_notice_to_room(order.room, message, True)

                return Response(OrderSerializer(order).data, status = status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def confirm_request(request, pk):
    try:
        order = Order.objects.get(pk = pk)
        cur_user = request.user
        if order.user.id == cur_user.id:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        else:
            if order.is_cancelled or order.is_replied:
                return Response(status = status.HTTP_406_NOT_ACCEPTABLE)
            else:
                order.is_replied = True
                order.is_accepted = True
                order.status = 3
                order.save()

                # create join
                cast = order.user if order.user.role == 0 else order.target
                Join.objects.create(user = cast, order = order, status = 1, selection = 0)
                
                # send notification
                message = "個人オーダーのリクエストが確定しました。\n\
                    素敵な時間をお過ごしください♪"
                # order.room.status = 2
                order.room.last_message = message
                order.room.save()

                send_notice_to_room(order.room, message, True)

                # send room event 'confirmed'
                send_room_event('confirmed', order.room)

                # create order
                return Response(OrderSerializer(order).data, status = status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

class ReviewView(mixins.CreateModelMixin, mixins.ListModelMixin, generics.GenericAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    queryset = Review.objects.all()

    def get_queryset(self):
        user_id = int(self.request.GET.get("user_id", "0"))
        if user_id > 0:
            return Review.objects.filter(target_id = user_id).order_by('-created_at')
        else:
            return Review.objects.all().order_by('-created_at')

    def get(self, request, *args, **kwargs):
        total = self.get_queryset().count()
        paginator = Paginator(self.get_queryset().order_by('-created_at'), 10)
        page = int(request.GET.get("page", "1"))
        reviews = paginator.page(page)

        return Response({"total": total, "results": ReviewSerializer(reviews, many=True).data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_reviews(request, id):
    try:
        cur_order = Order.objects.get(pk = id)
        if cur_order.reviews.filter(source = request.user).count() > 0:
            return Response({"result": True, "data": ReviewSerializer(cur_order.reviews.filter(source = request.user), many = True).data})
        else:
            user_ids = []
            if cur_order.is_private:
                target = cur_order.user if cur_order.user.id != request.user.id else cur_order.target
                user_ids = [target.id]
            else:
                if request.user.role == 1:
                    user_ids = list(cur_order.joins.filter(status = 1, is_ended = True).values_list('user_id', flat = True))
                else:
                    user_ids = [cur_order.user.id]
            return Response({"result": False, "data": MainInfoSerializer(Member.objects.filter(id__in = user_ids), many = True).data})
    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAdminPermission])
def complete_payment(request, id):
    try:
        order = Order.objects.get(pk = id)
        if order.status != 5:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        else:
            order.status = 7
            order.save()
            return Response(OrderSerializer(order).data, status = status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAdminPermission])
def fail_payment(request, id):
    try:
        order = Order.objects.get(pk = id)
        if order.status != 5:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        else:
            order.status = 10
            order.save()
            return Response(OrderSerializer(order).data, status = status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAdminPermission])
def get_schedule_data(request):
    page = int(request.GET.get('page', "1"))
    cur_query = request.GET.get("query", "")
    size = int(request.GET.get('size', "100"))

    if cur_query != "":
        try:
            query_obj = json.loads(cur_query)
        except:
            return Response({"total": 0, "results": []}, status=status.HTTP_200_OK)

        query_date = query_obj.get('date', "")
        is_present = query_obj.get('present', False)
        type_val = query_obj.get('type', "all")
        start_time = None
        end_time = None

        if query_date != "":
            start_time = datetime.strptime("{}-+0900".format(query_date), "%Y-%m-%d-%z")
            start_time = start_time.astimezone(pytz.timezone('UTC'))
            end_time = start_time + timedelta(days = 1)

        memberQuery = Member.objects.filter(role = 0, is_active = True)
        if is_present:
            memberQuery = memberQuery.filter(is_present = True)

        total = memberQuery.count()       
        users = memberQuery.all()[(page - 1) * size:page * size]
        
        if start_time == None:
            start_time = timezone.now()

        return_array = []
        for user in users:
            cur_obj = {}
            cur_obj["user"] = MainInfoSerializer(user).data
            cur_obj["schedules"] = []

            join_query = user.joins

            if type_val == "confirm":
                join_query = join_query.filter(status = 1)
            elif type_val == "select":
                join_query = join_query.filter(selection = 1)
            elif type_val == "applying":
                join_query = join_query.filter(status = 0, selection = 0)

            for join in join_query.filter(ended_at__gt = start_time, started_at__lt = end_time).order_by("started_at"):
                cur_obj["schedules"].append(JoinSerializer(join).data)
            
            return_array.append(cur_obj)

        return Response({ "total": total, "results": return_array })
    else:
        return Response(status = status.HTTP_400_BAD_REQUEST)