from django.urls import path, include
from .views import *
from django.conf.urls import url

urlpatterns = [
    # authorization
    path('email/register', EmailRegisterView.as_view(), name = "email_view"),
    path('email/login', EmailLoginView.as_view(), name = "email_login"),
    path('line/login', LineLoginView.as_view(), name = "line_login"),
    path('<str:email>/<str:email_token>', verify_email, name="verify_token"),

    # after authorization
    path('info', get_user_profile, name = "user_info"),
]