"""
API URLs for Accounts
"""

from django.urls import path, include

from .views.auth import *
from .views.member import *

urlpatterns = [
    # account management
    path('admins', AdminView.as_view(), name = "admin_view"),
    path('admins/<int:pk>', AdminView.as_view(), name = "admin_detail_view"),

    # member management
    path('members', MemberView.as_view(), name = "member_view"),
    
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
    path('avatars/order', change_avatar_order, name = "avatar_change_order"),
    path('avatars/<int:pk>', AvatarView.as_view(), name = "avatar_detail_view"),

    # update profile
    path('member/line', change_line, name = "avatar_view"),
    path('member/password', change_password, name = "password_change"),
    path('member/profile', ProfileView.as_view(), name = "update_profile"),
    path('member/choice', edit_choice, name = "edit_choice"),

    # detail profile
    path('details', DetailView.as_view(), name = "detail_view"),
    path('details/<int:pk>', DetailView.as_view(), name = "detail_detail_view"),

    # tweet
    path('tweets', TweetView.as_view(), name = "tweet_view"),
    path('tweets/<int:pk>', TweetView.as_view(), name = "tweet_detail_view"),
    path('count-tweet', count_tweet, name = "tweet_count"),
    path('toggle-tweet', toggle_tweet, name = "tweet_toggle"),

    # search
    path('casts/fresh', get_fresh_casts, name = "fresh_casts"),
    path('casts/search', search_casts, name = "search_casts"),
    path('guests/search', search_guests, name = "search_guests"),
]
