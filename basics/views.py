from django.shortcuts import render
from rest_framework.serializers import Serializer
from rest_framework_jwt.views import JSONWebTokenAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission, SAFE_METHODS
from rest_framework.response import Response
from rest_framework import generics, status, mixins
from rest_framework.parsers import JSONParser 
from rest_framework.views import APIView
from .serializers import *
from django.db.models.deletion import ProtectedError
from .models import Location, CastClass, Choice, GuestLevel

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
            input_data = serializer.data
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

