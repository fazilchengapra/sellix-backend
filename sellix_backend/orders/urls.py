from django.urls import path
from .views import OrderListCreateView, OrderDetailView

urlpatterns = [
    path("<str:order_id>", OrderDetailView.as_view(), name="order-detail"),
    path("", OrderListCreateView.as_view(), name="order-list-create"),
]
