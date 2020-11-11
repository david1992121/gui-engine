from django.shortcuts import render
from django.db.models.deletion import ProtectedError

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission, SAFE_METHODS
from rest_framework.response import Response
from rest_framework import generics, status, mixins
from rest_framework.parsers import JSONParser 
from rest_framework.views import APIView

from .serializers import *
from .models import *
from accounts.serializers.auth import MemberSerializer

# Create your views here.
class IsAdminPermission(BasePermission):
    message = "Only admin is allowed to update info"

    def has_permission(self, request, view):
        return request.user.role < 0
class LocationView(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    
    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "DELETE", "UPDATE"]:
            self.permission_classes = [IsAdminPermission]
        else:
            self.permission_classes = [IsAuthenticated]
        
        return super(LocationView, self).get_permissions()
    
    def get(self, request):
        id_num = int(request.query_params.get("pid", "0"))
        shown = int(request.query_params.get("shown", "0"))
        queryset = Location.objects
        if id_num > 0:            
            queryset = queryset.filter(parent__id = id_num)
        else:
            queryset = queryset.filter(parent = None)
        if shown == 1:
            queryset = queryset.filter(shown = True)
        queryset = queryset.order_by('order')
        serializer = self.get_serializer(queryset, many = True)
        return Response(serializer.data, status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        if request.data['parent'] != None:
            request.data['parent'] = request.data['parent']['id']
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

class LocationChangeOrder(APIView):
    def post(self, request):
        serializer = LocationSerializer(data = request.data, many = True)
        if serializer.is_valid():
            input_data = serializer.validated_data
            for item in input_data:
                cur_id = item.pop('id')
                Location.objects.filter(pk = cur_id).update(**item)                
            return Response({ "success": True})
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        
class ClassesView(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = CastClass.objects.all()
    serializer_class = ClassesSerializer
    
    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "DELETE", "UPDATE"]:
            self.permission_classes = [IsAdminPermission]
        else:
            self.permission_classes = [IsAuthenticated]
        
        return super(ClassesView, self).get_permissions()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class LevelsView(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = GuestLevel.objects.all()
    serializer_class = LevelsSerializer
    
    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "DELETE", "UPDATE"]:
            self.permission_classes = [IsAdminPermission]
        else:
            self.permission_classes = [IsAuthenticated]
        
        return super(LevelsView, self).get_permissions()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class ChoiceView(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    pagination_class = ChoicePagination
    
    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "DELETE", "UPDATE"]:
            self.permission_classes = [IsAdminPermission]
        else:
            self.permission_classes = [IsAuthenticated]
        
        return super(ChoiceView, self).get_permissions()

    def get_queryset(self):
        return Choice.objects.order_by('-category', 'subcategory', 'order')

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class ReceiptView(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = ReceiptSetting.objects.all()
    serializer_class = ReceiptSerializer    
    
    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "DELETE", "UPDATE"]:
            self.permission_classes = [IsAdminPermission]
        else:
            self.permission_classes = [IsAuthenticated]
        
        return super(ReceiptView, self).get_permissions()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

class BannerView(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer

    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "DELETE", "UPDATE"]:
            self.permission_classes = [IsAdminPermission]
        else:
            self.permission_classes = [IsAuthenticated]
        
        return super(BannerView, self).get_permissions()
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class SettingView(mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Setting.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = SettingSerializer
        
    def post(self, request, *args, **kwargs):
        cur_user = request.user
        serializer = self.get_serializer(data = request.data)
        if serializer.is_valid():
            setting_obj = serializer.save()
            cur_user.setting = setting_obj
            cur_user.save()
            return Response(MemberSerializer(cur_user).data, status.HTTP_200_OK)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

class GiftView(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = Gift.objects.all()
    serializer_class = GiftSerializer
    pagination_class = GiftPagination

    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "DELETE", "UPDATE"]:
            self.permission_classes = [IsAdminPermission]
        else:
            self.permission_classes = [IsAuthenticated]
        
        return super(GiftView, self).get_permissions()
    
    def get(self, request, *args, **kwargs):
        is_shown = request.GET.get('is_shown', "")
        if is_shown != "":
            queryset = Gift.objects.filter(is_shown = True)
            return Response(GiftSerializer(queryset, many = True).data, status = status.HTTP_200_OK)
        else:
            return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class CostPlanView(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = CostPlan.objects.all()
    serializer_class = CostplanSerializer
    pagination_class = CostplanPagination

    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "DELETE", "UPDATE"]:
            self.permission_classes = [IsAdminPermission]
        else:
            self.permission_classes = [IsAuthenticated]
        
        return super(CostPlanView, self).get_permissions()
    
    def get(self, request, *args, **kwargs):
        location_id = int(request.GET.get('location', "0"))
        if location_id > 0:
            queryset = CostPlan.objects.filter(location_id = location_id, is_shown = True)
            return Response(CostplanSerializer(queryset, many = True).data, status = status.HTTP_200_OK)
        else:
            return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)