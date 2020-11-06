"""
API URLs for Basics
"""

from django.urls import path, include

from .views import *

urlpatterns = [
    # location
    path('locations', LocationView.as_view(), name="location_view"),
    path('locations/<int:pk>', LocationView.as_view()),
    path('locations/changeOrder', LocationChangeOrder.as_view()),

    # class
    path('classes', ClassesView.as_view(), name="classes_view"),
    path('classes/<int:pk>', ClassesView.as_view(), name="classes_detail_view"),

    # matching choices
    path('choices', ChoiceView.as_view(), name="chioces_view"),
    path('choices/<int:pk>', ChoiceView.as_view(), name="chioces_detail_view"),
]