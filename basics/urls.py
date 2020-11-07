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

    # level
    path('levels', LevelsView.as_view(), name="levels_view"),
    path('levels/<int:pk>', LevelsView.as_view(), name="levels_detail_view"),

    # matching choices
    path('choices', ChoiceView.as_view(), name="chioces_view"),
    path('choices/<int:pk>', ChoiceView.as_view(), name="chioces_detail_view"),

    # receipt
    path('receipt', ReceiptView.as_view(), name = "receipt_view"),
    path('receipt/<int:pk>', ReceiptView.as_view(), name = "receipt_detail_view"),

    # banner
    path('banners', BannerView.as_view(), name = "banner_view"),
    path('banners/<int:pk>', BannerView.as_view(), name = "banner_detail_view"),

    # setting
    path('settings', SettingView.as_view(), name = "setting_view"),
    path('settings/<int:pk>', SettingView.as_view(), name = "setting_detail_view")
]