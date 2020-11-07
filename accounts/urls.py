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
    path('verify/<str:email>/<str:email_token>', verify_email, name="verify_token"),
    path('resend', resend_email, name="resend_email"),
    path('password/', include('django_rest_passwordreset.urls',
                              namespace='password_reset')),
    path('admin/login', AdminLoginView.as_view(), name="admin_login"),

    # get info
    path('info', get_user_profile, name="user_info"),   

    # upload info
    path('initialize', InitialRegister.as_view(), name="info_register"),

    # update info
    path('avatars', AvatarView.as_view(), name = "avatar_view"),
    path('avatars/<int:pk>', AvatarView.as_view(), name = "avatar_detail_view"),

    # tweet
    path('tweets', TweetView.as_view(), name = "tweet_view"),
    path('tweets/<int:pk>', TweetView.as_view(), name = "tweet_view"),
    path('toggle-tweet', toggle_tweet, name = "tweet_toggle"),
]
