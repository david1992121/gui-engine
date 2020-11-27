"""
URLs for Chat
"""
from django.urls import path

from .views import *

urlpatterns = [
    # path('', views.index, name='index'),
    # path('<str:room_name>/', views.room, name='room'),
    path('notices', notices_list, name="notice_list"),
    path('rooms', room_list, name="room_list"),
    path('rooms/<int:room_id>', room_detail, name="room_detail"),
    path('rooms/<int:room_id>/messages', message_list, name="message_list"),
    path('unread', unread_count, name="unread_count"),

    # user chatrooms for admin
    path('chatrooms', ChatroomView.as_view(), name="user_chat_rooms"),

    # notices for admin
    path('notices_admin', AdminNoticeView.as_view(), name="admin_notices"),
    path('notices_admin/<int:pk>', AdminNoticeView.as_view(), name="admin_detail_notices"),

    # messages for user
    path('messages/upload', upload_images, name = "message_upload"),

    # messages
    path('messages', MessageView.as_view(), name = "message_view"),
    path('messages/users', MessageUserView.as_view(), name = "message_user"),
    path('messages/users/count', get_user_count, name = "message_user_count"),
    path('messages/admin/send', send_bulk_messages, name = "send_message"),
]
