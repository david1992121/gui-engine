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
    
]