from django.urls import path
from .views import (
    SalesAnalyticsView,
    RevenueTrendView,
    SalesByCategoryView,
    OrderStatusView,
    TopSellingProductsView,
)

urlpatterns = [
    path("", SalesAnalyticsView.as_view(), name="sales-analytics"),
    path("revenue-trend/", RevenueTrendView.as_view(), name="revenue-trend"),
    path("sales-by-category/", SalesByCategoryView.as_view(), name="sales-by-category"),
    path("order-status/", OrderStatusView.as_view(), name="order-status"),
    path(
        "top-selling-products/",
        TopSellingProductsView.as_view(),
        name="top-selling-products",
    ),
]
