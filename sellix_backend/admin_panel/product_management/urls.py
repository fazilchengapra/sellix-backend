from django.urls import path
from .views import ProductListView, ProductCreateView, ProductUpdateView

urlpatterns = [
    # Define your product management URLs here
    path("list/", ProductListView.as_view(), name="product-list"),
    path("create/", ProductCreateView.as_view(), name="product-create"),
    path("<int:pk>/update/", ProductUpdateView.as_view(), name="product-update"),
]
