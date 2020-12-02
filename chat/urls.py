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
    path('messages/admin/unread', get_unread_admin_messages, name = "admin_unread_message"),
    path('messages/admin/unread/count', get_unread_admin_messages_count, name = "admin_unread_message_count"),
    path('messages/delete/<int:id>', delete_message, name = "delete_message"),
    path('messages/change/<int:id>', change_message_state, name = "change_message_state"),
    
    # admin all rooms
    path('all_rooms', get_all_rooms, name = "all_rooms_view"),

    # admin rooms
    path('admin/rooms', RoomView.as_view(), name = "admin_rooms"),
    path('admin/rooms/<int:pk>', RoomDetailView.as_view(), name = "admin_detail_room"),
    path('admin/rooms/<int:pk>/messages', RoomMessageView.as_view(), name = "admin_room_messages"),
    path('admin/rooms/<int:pk>/users', add_member, name = "add_member"),
]
