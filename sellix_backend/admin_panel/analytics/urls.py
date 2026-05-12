from django.urls import path
from .views import SalesAnalyticsView, RevenueTrendView

urlpatterns = [
    path("", SalesAnalyticsView.as_view(), name="sales-analytics"),
    path("revenue-trend/", RevenueTrendView.as_view(), name="revenue-trend"),
]
