from django.urls import path

from .views import AdminOrderDetailView, AdminOrderListView

urlpatterns = [
    path("", AdminOrderListView.as_view(), name="admin-order-list-create"),
    path("<int:pk>/", AdminOrderDetailView.as_view(), name="admin-order-detail"),
]
