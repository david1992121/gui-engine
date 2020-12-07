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
    path('orders/<int:pk>', OrderDetailView.as_view(), name = "admin_detail_order"),
    path('orders/<int:id>/apply', apply_order, name = "cast_apply_order"),
    path('orders/<int:id>/confirm/<int:user_id>', confirm_cast, name = "cast_confirm"),
    path('orders/counts', get_order_counts, name = "admin_order_counts"),
    path('month_data', get_month_data, name = "admin_month_data"),

    # cast order
    path('orders/cast', OrderCastView.as_view(), name = "cast_order"),

    # entry cast management
    path('joins', JoinView.as_view(), name = "joins_view"),
    path('joins/<int:pk>', JoinView.as_view(), name = "joins_view"),
    path('joins/<int:id>/drop', drop_join, name = "drop_join"),
    path('joins/<int:id>/recover', recover_join, name = "recover_join")
]
