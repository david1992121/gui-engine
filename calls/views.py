from inspect import formatargvalues
import json, pytz
from datetime import datetime, timedelta

from django.db.models import Sum, Q, Count, F
from django.db.models import query
from django.core.paginator import Paginator
from django.utils import timezone
from dateutil.parser import parse
from accounts.views.member import IsAdminPermission, IsCastPermission, IsSuperuserPermission, IsGuestPermission

from rest_framework import status
from rest_framework import generics
from rest_framework import mixins
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import *
from .utils import send_call, send_applier
from chat.utils import send_super_message, send_room_to_users
from chat.models import Room, Message

# Create your views here.
class InvoiceView(mixins.CreateModelMixin, mixins.ListModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get(self, request, *args, **kwargs):
        page = int(request.GET.get('page', "1"))
        cur_request = request.query_params.get("query", "")

        # user type
        query_set = Invoice.objects

        # query
        if cur_request != "":
            try:
                query_obj = json.loads(cur_request)
            except:
                return Response({"total": 0, "results": []}, status=status.HTTP_200_OK)

            # location
            location_val = query_obj.get("location_id", 0)
            if location_val > 0:
                query_set = query_set.filter(location_id=location_val)

            # invoice type
            invoice_type = query_obj.get("invoice_type", "")
            if invoice_type != "":
                query_set = query_set.filter(invoice_type = invoice_type)

            # point_user_id
            point_user_id = query_obj.get("point_user_id", 0)
            point_receiver_id = query_obj.get("point_receiver_id", 0)

            if point_user_id > 0:
                query_set = query_set.filter(giver_id = point_user_id)
            else:
                if point_receiver_id > 0:
                    query_set = query_set.filter(taker_id = point_receiver_id)

                        # transfer from
            date_from = query_obj.get("from", "")
            if date_from != "":
                from_date = parse(date_from)
                query_set = query_set.filter(
                    created_at__date__gte=from_date.strftime("%Y-%m-%d"))

            # transfer to
            date_to = query_obj.get("to", "")
            if date_to != "":
                to_date = parse(date_to)
                query_set = query_set.filter(
                    created_at__date__lte=to_date.strftime("%Y-%m-%d"))

        total = query_set.count()
        paginator = Paginator(query_set.order_by('-created_at'), 10)
        invoices = paginator.page(page)

        return Response({"total": total, "results": InvoiceSerializer(invoices, many=True).data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

@api_view(['GET'])
@permission_classes([IsSuperuserPermission])
def get_invoice_total(request):
    buy_point = Invoice.objects.filter(
        Q(invoice_type = 'BUY') | Q(invoice_type = 'CHARGE') | Q(invoice_type = 'AURO CHARGE')
    ).aggregate(Sum('take_amount'))['take_amount__sum']
    normal_invoices = Invoice.objects.exclude(invoice_type = 'CHARGE').exclude(invoice_type = 'BUY').exclude(invoice_type = 'AUTO_CHARGE')
    use_point = normal_invoices.aggregate(Sum('give_amount'))['give_amount__sum']
    pay_point = normal_invoices.aggregate(Sum('take_amount'))['take_amount__sum']
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
            time_filter &= Q(gave__created_at__date__gte = parse(date_from).strftime("%Y-%m-%d"))
        if date_to != "":
            time_filter &= Q(gave__created_at__date__lte = parse(date_to).strftime("%Y-%m-%d"))
        
        query_set = query_set.annotate(
            overall_points = Sum('gave__give_amount', filter=time_filter)
        ).order_by('-overall_points', '-call_times')
    else:        
        if date_from != "":
            time_filter &= Q(took__created_at__date__gte = parse(date_from).strftime("%Y-%m-%d"))
        if date_to != "":
            time_filter &= Q(took__created_at__date__lte = parse(date_to).strftime("%Y-%m-%d"))
        
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
                query_set = query_set.filter(status = status_val)
            
            if location_id > 0:
                query_set = query_set.filter(cost_plan_id = cost_plan_id)
            
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
            
            # call send
            cast_ids = list(Member.objects.filter(location = new_order.parent_location).values_list('id', flat = True).distinct())
            send_call(new_order, cast_ids, "create")

            send_super_message("system", request.user.id, message_content)
            return Response(OrderSerializer(new_order).data, status = status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(status = status.HTTP_400_BAD_REQUEST)

class OrderDetailView(mixins.RetrieveModelMixin, generics.GenericAPIView):
    permission_classes = (IsGuestPermission | IsSuperuserPermission, )
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

@api_view(['GET'])
@permission_classes([IsAdminPermission])
def get_order_counts(request):
    is_normal = int(request.GET.get('is_normal', '1'))
    status_array = []
    if is_normal == 1:
        status_title = [
            'Collecting customers', 'Selecting Cast Name',
            'Cast Confirmed', 'Meeting Finished', 'Finished(Not Paid Yet)',
            'Pay Finished', 'Cancel with not enough casts'
        ]
        status_numbers = [0, 1, 3, 5, 6, 7, 8]
        for index, status_number in enumerate(status_numbers):
            orders_count = Order.objects.filter(status = status_number).count()
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
        query_set = Order.objects.annotate(joined_count = Count('joined')).filter(status = 0, joined_count__lt = F('person'))
        orders_count = query_set.count()
        ids_array = list(query_set.values_list('id', flat = True).distinct())

        status_array.append({
            "title": "Collecting Cast + Not Enough",
            "count": orders_count,
            "ids_array": ids_array,
            "value": 0
        })

        # cast confirm + start time exceeds
        query_set = Order.objects.filter(status = 3, meet_time_iso__gt = timezone.localtime())
        orders_count = query_set.count()
        ids_array = list(query_set.values_list('id', flat = True).distinct())
        
        status_array.append({
            "title": "Cast Confirm + Start Time Exceeds",
            "count": orders_count,
            "ids_array": ids_array,
            "value": 0
        })

        # extended time exceeds
        ended_predict = timezone.now() - timedelta(days = 8)
        query_set = Order.objects.filter(status = 4, ended_at__lt = ended_predict)
        orders_count = query_set.count()
        ids_array = list(query_set.values_list('id', flat = True).distinct())
        
        status_array.append({
            "title": "Extened time exceeds 8 hours",
            "count": orders_count,
            "ids_array": ids_array,
            "value": 0
        })

        # payment failed
        query_set = Order.objects.filter(status = 9)
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

class JoinView(mixins.UpdateModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAdminPermission]
    serializer_class = JoinSerializer
    queryset = Join.objects.all()

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

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

        query_set = Order.objects.filter(parent_location = cur_user.location)

        today_date = datetime.now(pytz.timezone("Asia/Tokyo"))
        today_date = today_date.replace(hour = 0, minute = 0, second = 0, microsecond = 0)

        tomorrow_date = today_date + timedelta(days = 1)
        if mode == 'today':
            query_set = query_set.filter(status__lt = 3, meet_time_iso__gte = today_date, meet_time_iso__lt = tomorrow_date)
        elif mode == 'tomorrow':
            query_set = query_set.filter(status__lt = 3, meet_time_iso__gte = tomorrow_date)
        else:
            query_set = query_set.filter(joins__user = cur_user)

        query_set = query_set.order_by('-created_at')
        paginator = Paginator(query_set, 5)
        orders = paginator.page(page)

        return Response(OrderSerializer(orders, many=True).data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsCastPermission])
def apply_order(request, id):
    try:
        cur_order = Order.objects.get(pk = id)
        newJoin = Join.objects.create(user = request.user, order = cur_order)
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
            send_applier(cur_order.id, cur_order.user.id)

        # inform applier to casts
        cur_order = Order.objects.get(pk = id)

        cast_ids = list(Member.objects.filter(location = cur_order.parent_location).values_list('id', flat = True).distinct())
        send_call(cur_order, cast_ids, "update")

        return Response(JoinSerializer(newJoin).data)

    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsGuestPermission])
def confirm_cast(request, id, user_id):
    try:
        cur_order = Order.objects.get(pk = id)

        # if it has already been confirmed
        if cur_order.status >= 3:
            return Response(status = status.HTTP_403_FORBIDDEN)
        
        # else
        curUser = Member.objects.get(pk = user_id)

        if cur_order.joins.filter(user__id = curUser.id).count() == 0:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        else:
            cur_order.joins.filter(user__id = curUser.id).update(status = 1, selection = 1)
            room_created = False
            room_id = 0

            # if confirmed person fills
            if cur_order.joins.filter(status = 1, selection = 1).count() == cur_order.person:

                # create new room and message           
                user_ids = [cur_order.user]
                user_ids = user_ids + list(cur_order.joins.filter(status = 1, selection = 1).values_list("user_id", flat = True))

                new_message = "おめでとうございます♪ \n \
                    マッチングが確定しました♪ \n \
                    ゲストさんはキャストさんへお店の場所を教えてあげて下さい。\n \
                    キャストさんはゲストさんへ到着予定時間をお伝え下さい。\n \
                    それでは素敵な時間をお過ごしください。"
                location_name = cur_order.location.name if cur_order.location != None else cur_order.location_other
                date_str = cur_order.meet_time_iso.astimezone(pytz.timezone("Asia/Tokyo")).strftime("%Y{0}%m{1}%d{2}%H{3}%M{4}").format(*"年月日時分")
                room_title = "合流：{0} {1} キャスト{2}人".format(location_name, date_str, cur_order.person)
                new_room = Room.objects.create(
                    last_message = new_message, room_type = "public", room_title = room_title, 
                    is_group = True, last_sender = Member.objects.get(username = "system"))
                new_room.users.set(user_ids)

                send_room_to_users(new_room, user_ids, "create")
                room_id = new_room.id
                room_created = True                
                
            # send confirm to cast
            send_call(cur_order, [curUser.id], "confirm")

            return Response({ "created": room_created, "room": room_id }, status = status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response(status = status.HTTP_400_BAD_REQUEST)