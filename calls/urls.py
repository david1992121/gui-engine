"""
API URLs for Calls
"""

from django.urls import path, include

from .views import *

urlpatterns = [
    # account management
    path('invoices', InvoiceView.as_view(), name = "invoice_view"),
    path('ranking', get_rank_users, name = "get_ranking"),

    # admin point statistics
    path('admin_invoices', get_invoice_total, name = "admin_invoice"),

    # admin order
    path('orders', OrderView.as_view(), name = "admin_order"),
    path('orders/<int:pk>', OrderDetailView.as_view(), name = "admin_detail_order")
]
