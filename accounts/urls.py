"""
API URLs for Accounts
"""

from django.urls import path, include

from .views.auth import *
from .views.member import *

urlpatterns = [
    # authorization
    path('email/register', EmailRegisterView.as_view(), name="email_view"),
    path('email/login', EmailLoginView.as_view(), name="email_login"),
    path('line/login', LineLoginView.as_view(), name="line_login"),
    path('<str:email>/<str:email_token>', verify_email, name="verify_token"),
    path('resend/<int:id>', resend_email, name="resend_email"),
    path('password/', include('django_rest_passwordreset.urls',
                              namespace='password_reset')),

    # get info
    path('info', get_user_profile, name="user_info"),   

    # upload info
    path('initialize', InitialRegister.as_view(), name="info_register")
]
