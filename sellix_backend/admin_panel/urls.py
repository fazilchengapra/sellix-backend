from django.urls import path, include

urlpatterns = [
    path("dashboard/", include("admin_panel.dashboard.urls")),
]
