"""
API URLs for Accounts
"""

from django.urls import path, include

from .views.auth import *
from .views.member import *

urlpatterns = [
    # account management
    path('admins', AdminView.as_view(), name="admin_view"),
    path('admins/<int:pk>', AdminView.as_view(), name="admin_detail_view"),

    # user management
    path('users', UserView.as_view(), name="user_view"),
    path('users/<int:pk>', UserDetailView.as_view(), name="user_detail_view"),

    path(
        'users/toggle_active/<int:id>',
        toggle_active,
        name="user_active_toggle"),
    path('users/to_cast/<int:id>', to_cast, name="user_to_cast"),
    path('users/check', check_user_exist, name="check_user_exist"),

    # user thumbnails
    path('thumbnails', add_thumbnails, name="user_add_thumbnail"),
    path('thumbnails/delete', remove_thumbnail, name="user_remove_thumbnail"),

    # user choices
    path('choices', set_choices, name="user_set_choice"),

    # member management
    path('members', MemberView.as_view(), name="member_view"),
    path('members/<int:pk>', MemberDetailView.as_view(), name="member_view"),
    path('members/<int:member_id>/apply', member_apply, name="member_apply"),
    path('casts', CastView.as_view(), name="cast_view"),

    # authorization
    path('email/register', EmailRegisterView.as_view(), name="email_view"),
    path('email/login', EmailLoginView.as_view(), name="email_login"),
    path('line/login', LineLoginView.as_view(), name="line_login"),
    path('verify/<str:email>/<str:email_token>',
         verify_email, name="verify_token"),
    path('resend', resend_email, name="resend_email"),
    path('password/', include('django_rest_passwordreset.urls',
                              namespace='password_reset')),
    path('admin/login', AdminLoginView.as_view(), name="admin_login"),

    # get info
    path('info', get_user_profile, name="user_info"),

    # upload info
    path('initialize', InitialRegister.as_view(), name="info_register"),

    # update info
    path('avatars', AvatarView.as_view(), name="avatar_view"),
    path('avatars/order', change_avatar_order, name="avatar_change_order"),
    path('avatars/<int:pk>', AvatarView.as_view(), name="avatar_detail_view"),

    # update profile
    path('member/line', change_line, name="avatar_view"),
    path('member/password', change_password, name="password_change"),
    path('member/profile', ProfileView.as_view(), name="update_profile"),
    path('member/choice', edit_choice, name="edit_choice"),

    # detail profile
    path('details', DetailView.as_view(), name="detail_view"),
    path('details/<int:pk>', DetailView.as_view(), name="detail_detail_view"),

    # tweet
    path('tweets', TweetView.as_view(), name="tweet_view"),
    path('tweets/<int:pk>', TweetView.as_view(), name="tweet_detail_view"),
    path('count-tweet', count_tweet, name="tweet_count"),
    path('toggle-tweet', toggle_tweet, name="tweet_toggle"),

    # search
    path('casts/fresh', get_fresh_casts, name="fresh_casts"),
    path('casts/present', get_present_casts, name="present_casts"),
    path('casts/search', search_casts, name="search_casts"),
    path('guests/search', search_guests, name="search_guests"),

    # transfer info
    path('casts/transfer', apply_transfer, name="transfer_apply"),
    path(
        'casts/transfer_info',
        TransferInfoView.as_view(),
        name="transfer_info"),
    path(
        'casts/transfer_info/<int:pk>',
        TransferInfoView.as_view(),
        name="transfer_info"),

    # transfer view
    path('transfers', TransferView.as_view(), name="transfer_view"),
    path('transfers/count', count_transfer, name="count_transfer"),
    path(
        'transfers/proceed/<int:id>',
        proceed_transfer,
        name="proceed_transfer"),

    # favorite
    path('favorites/<int:id>', like_person, name="like_person"),

    # count users
    path('count', get_user_statistics, name="user_statistics"),

    # toggle present
    path('toggle_present', toggle_present, name="toggle_present"),

    # point buy
    path('point/buy', buy_point, name="buy_point"),

    # make receipt pdf
    path('point/pdf', export_pdf, name="export_pdf"),

    # profile change nickname
    path('profile', update_admin_profile, name="update_admin_profile"),
]
