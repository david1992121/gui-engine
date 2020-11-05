"""
APIs for Accounts
"""

import json
from threading import Thread
from base64 import urlsafe_b64decode, urlsafe_b64encode
import jwt
import requests

from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import JSONWebTokenAPIView

from django_rest_passwordreset.signals import reset_password_token_created

from accounts.models import Member
from accounts.serializers.auth import *

class EmailLoginView(JSONWebTokenAPIView):
    serializer_class = EmailJWTSerializer

class AdminLoginView(JSONWebTokenAPIView):
    serializer_class = AdminEmailJWTSerializer
class LineLoginView(APIView):
    """APIs for LINE Authorization"""
    permission_classes = [AllowAny]

    def get_token(self, obj):
        """Generate JWT Token"""
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

    def post(self, request):
        """Authorize with LINE"""
        serializer = SNSAuthorizeSerializer(data=request.data)

        if serializer.is_valid():
            line_code = serializer.data.get('code')
            role = serializer.data.get('role')

            url = "https://api.line.me/oauth2/v2.1/token"

            payload = 'grant_type=authorization_code' + \
                '&code=' + line_code + \
                '&redirect_uri=' + settings.CLIENT_URL + '/account/result' + \
                '&client_id=' + settings.LINE_CLIENT_ID + \
                '&client_secret=' + settings.LINE_CLIENT_SECRET

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.request(
                "POST", url, headers=headers, data=payload)

            id_token = json.loads(
                response.text.encode('utf8')).get('id_token', '')

            try:
                decoded_payload = jwt.decode(id_token, None, None)
                line_id = decoded_payload['sub']
                line_email = decoded_payload['email']
                role = int(decoded_payload['nonce'])

                user_obj, is_created = Member.objects.get_or_create(
                    email=line_email
                )

                if is_created:
                    user_obj.username = 'user_{}'.format(user_obj.id)

                if role == 0 and user_obj.role == 1:
                    user_obj.role = 10

                user_obj.social_id = line_id
                user_obj.social_type = 1
                user_obj.is_verified = True
                user_obj.save()

                return Response({
                    'token': self.get_token(user_obj),
                    'user': MemberSerializer(user_obj).data,                    
                }, status.HTTP_200_OK)

            except jwt.exceptions.InvalidSignatureError:
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status.HTTP_400_BAD_REQUEST)


class EmailRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Signup with Email"""
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
                user = Member.objects.create(email=email)
                user.username = "user_{}".format(user.id)
                user.set_password(password)
                user.save()

                to_email = [user.email]
                cur_token = default_token_generator.make_token(user)
                email = urlsafe_b64encode(str(user.email).encode('utf-8'))

                # now send email
                mail_subject = 'メールを確認してください'
                message = render_to_string('emails\\email_verification.html', {
                    'site_url': settings.SITE_URL,
                    'token': f'verify/{email.decode("utf-8")}/{cur_token}',
                })

                t = Thread(target=send_mail, args=(
                    mail_subject, message, settings.EMAIL_FROM_USER, to_email))
                t.start()

                return Response({
                    "success": True,
                    "user": MemberSerializer(user).data
                }, status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


def sendmail_thread(mail_subject, message, from_email, to_email, template):
    """Send Email using thread"""
    send_mail(mail_subject, message, from_email,
              to_email, html_message=template)


def verify_token(email, email_token):
    """Return token verification result"""
    try:
        users = Member.objects.filter(
            email=urlsafe_b64decode(email).decode("utf-8"))
        for user in users:
            print("user found")
            valid = default_token_generator.check_token(user, email_token)
            if valid:
                user.is_verified = True
                user.save()
                return valid
    except:
        pass
    return False


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, email, email_token):
    """Verify Email"""
    try:
        target_link = settings.CLIENT_URL + "/account/result?type=email_verified"
        if verify_token(email, email_token):
            return redirect(target_link)
        else:
            return render(
                request,
                "emails\\email_error.html",
                {'success': False, 'link': target_link}
            )
    except:
        pass


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """Get User Information"""
    cur_user = request.user
    serializer = MemberSerializer(cur_user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_email(request):
    """Resend Verification Email"""
    email = request.data.get('email', "")
    user = Member.objects.get(email = email)

    if user and not user.is_verified:
        # now send email
        to_email = [user.email]
        cur_token = default_token_generator.make_token(user)
        mail_subject = 'メールを確認してください'
        message = render_to_string('emails\\email_verification.html', {
            'site_url': settings.SITE_URL,
            'token': f'{user.email.decode("utf-8")}/{cur_token}',
        })

        t = Thread(target=sendmail_thread, args=(
            mail_subject, message, settings.EMAIL_FROM_USER, to_email))
        t.start()

        return Response(status.HTTP_200_OK)
    else:
        return Response(status.HTTP_400_BAD_REQUEST)


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):

    target_link = "{}/account/result?type=reset_password&token={}".format(
        settings.CLIENT_URL, reset_password_token.key)
    html_template = render_to_string(
        "emails\\password_forgotten.html", {'link': target_link})
    print(reset_password_token.user.email)

    mail_subject = "パスワードリセット"
    message = "パスワードトークンを確認してください"
    from_user = settings.EMAIL_FROM_USER
    receipient = [reset_password_token.user.email]

    t = Thread(target=sendmail_thread, args=(
        mail_subject, message, from_user, receipient, html_template))
    t.start()
