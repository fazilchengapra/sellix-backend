from django.urls import path
from .views import ProductListView

urlpatterns = [
    # Define your product management URLs here
    path("list/", ProductListView.as_view(), name="product-list"),
]
