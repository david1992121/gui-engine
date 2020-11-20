"""
URLs for Chat
"""
from django.urls import path

from . import views

urlpatterns = [
    # path('', views.index, name='index'),
    # path('<str:room_name>/', views.room, name='room'),
    path('notices', views.notices_list),
    path('rooms', views.room_list),
    path('rooms/<int:pk>', views.room_detail),
    path('unread', views.unread_count)
]
