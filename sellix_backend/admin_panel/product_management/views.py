from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from products.models import Product
from .serializers import ProductListSerializer
from .pagination import ProductPagination
from .filters import ProductFilter


class ProductListView(ListAPIView):
    queryset = Product.objects.prefetch_related("colors__images").all()
    serializer_class = ProductListSerializer
    pagination_class = ProductPagination

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_class = ProductFilter

    search_fields = [
        "name",
        "brand",
        "category",
    ]

    ordering_fields = [
        "price",
        "ratings",
        "reviews_count",
        "id",
    ]

    ordering = ["-id"]