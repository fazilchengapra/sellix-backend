from django.urls import path, include

urlpatterns = [
    path("dashboard/", include("admin_panel.dashboard.urls")),
    path("analytics/", include("admin_panel.analytics.urls")),
    path("product/", include("admin_panel.product_management.urls")),
    path("users/", include("admin_panel.user_management.urls")),
]
