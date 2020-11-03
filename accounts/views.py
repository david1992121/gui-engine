from django.shortcuts import render
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework import status, generics
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework_jwt.settings import api_settings
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission, SAFE_METHODS
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_jwt.views import JSONWebTokenAPIView

from .models import Member
from .tokens import account_activation_token
from .serializers import *

# Create your views here.
class EmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailRegisterSerializer(data=request.data)
        if serializer.is_valid():
            input_data = serializer.data
            email = input_data.get('email').strip()
            password = input_data.get('password')
            if Member.objects.filter(email=email).count() > 0:
                return Response({
                    "success": False,
                    "reason": "Email already exists"
                }, status.HTTP_200_OK)
            else:
                # create user
                user = Member.objects.create(email = email)
                user.set_password(password)
                user.save()
                
                # now send email
                current_site = get_current_site(request)
                mail_subject = 'メールを確認してください',
                message = render_to_string('email_templates\\email_verification.html', {
                    'site_url': settings.SITE_URL,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
                to_email = email
                send_mail(mail_subject, message, 'noreply@email.com', [to_email])
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
