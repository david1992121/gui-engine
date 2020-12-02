from django.db.models import Sum, Q, Count, F
from accounts.views.member import IsAdminPermission, IsSuperuserPermission
from dateutil.parser import parse
from datetime import timedelta
from django.utils import timezone
import json

from django.core.paginator import Paginator

from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework import generics
from rest_framework import mixins

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny, BasePermission

from .serializers import *

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
    permission_classes = [IsSuperuserPermission]
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

class OrderDetailView(mixins.RetrieveModelMixin, generics.GenericAPIView):
    permission_classes = [IsSuperuserPermission]
    serializer_class = [ OrderSerializer ]

    def get(self, request, *args, **kwargs):
        self.retrieve(request, *args, **kwargs)

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
                "value": status_number
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
            "value": ids_array
        })

        # cast confirm + start time exceeds
        query_set = Order.objects.filter(status = 3, meet_time_iso__gt = timezone.now())
        orders_count = query_set.count()
        ids_array = list(query_set.values_list('id', flat = True).distinct())
        
        status_array.append({
            "title": "Cast Confirm + Start Time Exceeds",
            "count": orders_count,
            "value": ids_array
        })

        # extended time exceeds
        ended_predict = timezone.now() - timedelta(days = 8)
        query_set = Order.objects.filter(status = 4, ended_at__lt = ended_predict)
        orders_count = query_set.count()
        ids_array = list(query_set.values_list('id', flat = True).distinct())
        
        status_array.append({
            "title": "Extened time exceeds 8 hours",
            "count": orders_count,
            "value": ids_array
        })

        
                

    return Response(status_array)