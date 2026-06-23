from django.urls import path
from .views import SalesAnalyticsView

urlpatterns = [
    path("", SalesAnalyticsView.as_view(), name="sales-analytics"),
]