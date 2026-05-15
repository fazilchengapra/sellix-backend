from django.urls import path
from .views import OrderListCreateView, OrderDetailView, OrderCancelView

urlpatterns = [
    path("<str:order_id>/", OrderDetailView.as_view(), name="order-detail"),
    path("", OrderListCreateView.as_view(), name="order-list-create"),
    path("<str:order_id>/cancel/", OrderCancelView.as_view(), name="order-cancel"),
]
