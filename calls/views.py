from datetime import timezone
from dateutil.parser import parse
import json

from django.core.paginator import Paginator

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
        page = request.GET.get('page', 1)
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
                query_set = query_set.filter(user_id = point_user_id, amount__lt =  0)
            else:
                if point_receiver_id > 0:
                    query_set = query_set.filter(user_id = point_receiver_id, amount__gte = 0)

                        # transfer from
            date_from = query_obj.get("from", "")
            if date_from != "":
                from_date = timezone(date_from)
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