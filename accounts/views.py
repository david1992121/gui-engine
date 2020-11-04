from django.shortcuts import render
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from base64 import urlsafe_b64decode, urlsafe_b64encode

from rest_framework import status, generics
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework_jwt.settings import api_settings
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission, SAFE_METHODS
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_jwt.views import JSONWebTokenAPIView

from .models import Member
from .serializers import *
from threading import Thread

class EmailLoginView(JSONWebTokenAPIView):
    serializer_class = EmailJWTSerializer

class LineLoginView(APIView):    
    
    def get_token(self, object):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(object)
        token = jwt_encode_handler(payload) 
        return token

    def post(self, request):
        serializer = SNSAuthorizeSerializer(data = request.data)
        if serializer.is_valid():
            input_data = serializer.data
            line_id = input_data.get('line_id')

            # line verification with line_id
            is_line_ok = True

            if is_line_ok:
                if Member.objects.filter(line_id = line_id).count() == 0:
                    Member.objects.create(line_id = line_id)

                user_obj = Member.objects.filter(line_id = line_id).first()
                return {
                    'token': self.get_token(user_obj),
                    'user': MemberSerializer(user_obj).data
                }
            
        return Response(status.HTTP_400_BAD_REQUEST)        

class EmailRegisterView(APIView):
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
                
                to_email = user.email
                cur_token = default_token_generator.make_token(user)
                email = urlsafe_b64encode(str(user.email).encode('utf-8'))

                # now send email
                mail_subject = 'メールを確認してください'
                message = render_to_string('emails\\email_verification.html', {
                    'site_url': settings.SITE_URL,                    
                    'token': f'{email.decode("utf-8")}/{cur_token}',
                })

                t = Thread(target = sendmail_thread, args = (mail_subject, message, "noreply@gmail.com", to_email))
                t.start()
            
            return Response({
                "success": True
            }, status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

# send email function 
def sendmail_thread(mail_subject, message, from_email, to_email):
    send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [to_email])

# verify token
def verify_token(email, email_token):
    try:
        users = get_user_model().objects.filter(email=urlsafe_b64decode(email).decode("utf-8"))
        for user in users:
            print("user found")
            valid = default_token_generator.check_token(user, email_token)
            if valid:
                user.is_verified = True
                user.save()
                return valid
    except b64Error:
        pass
    return False

# verify
@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, email, email_token):
    try:        
        target_link = settings.LOGIN_URL
        if verify_token(email, email_token):
            return redirect(target_link)
        else:
            return render(request, "emails\\email_error", {'success': false, 'link': target_link})
    except AttributeError:
        raise NotAllFieldCompiled('EMAIL_PAGE_TEMPLATE field not found')