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
]
