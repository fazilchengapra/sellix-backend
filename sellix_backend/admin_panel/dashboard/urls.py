from django.urls import path
from .views import DashboardView, OrdersOverview

urlpatterns = [
    path("", DashboardView.as_view()),
    path("orders-overview/", OrdersOverview.as_view()),
]
