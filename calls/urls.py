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

    # order
    path('orders', OrderView.as_view(), name = "order_view"),
    path('orders/<int:pk>', OrderDetailView.as_view(), name = "order_detail_view"),
    path('orders/<int:id>/apply', apply_order, name = "cast_apply_order"),
    path('orders/<int:id>/confirm/<int:user_id>', confirm_cast, name = "cast_confirm"),
    path('orders/<int:id>/room', make_room, name = "make_room"),
    path('orders/<int:id>/cancel', cancel_order, name = "cancel_order"),
    path('orders/<int:id>/auto', auto_match, name = "auto_match"),
    path('orders/counts', get_order_counts, name = "admin_order_counts"),
    path('month_data', get_month_data, name = "admin_month_data"),

    # admin create order
    path('admin/orders', create_order, name = "admin_order_create"),

    # cast order
    path('orders/cast', OrderCastView.as_view(), name = "cast_order"),

    # entry cast management
    path('joins', JoinView.as_view(), name = "joins_view"),
    path('joins/<int:pk>', JoinView.as_view(), name = "joins_view"),
    path('joins/<int:id>/drop', drop_join, name = "drop_join"),
    path('joins/<int:id>/recover', recover_join, name = "recover_join"),

    # get cast room joins
    path('rooms/<int:id>/check', check_meet_time, name = "check_meet_status"),
    path('rooms/<int:id>/joins', get_room_joins, name = "room_join"),
    path('rooms/<int:id>/joins/start', start_joins, name = "start_join"),
    path('rooms/<int:id>/joins/end', end_joins, name = "end_join"),
]
