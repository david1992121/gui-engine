"""
API URLs for Calls
"""

from django.urls import path, include

from .views import *

urlpatterns = [
    # account management
    path('invoices', InvoiceView.as_view(), name = "invoice_view"),
]
