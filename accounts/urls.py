from django.urls import path, include
from .views import *
from django.conf.urls import url

urlpatterns = [
    path('email', EmailView.as_view(), name = "email_view"),
]