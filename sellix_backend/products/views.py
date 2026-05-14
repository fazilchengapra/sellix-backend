from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from drf_spectacular.utils import extend_schema


from rest_framework.generics import ListAPIView, RetrieveAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Product
from .serializers import ProductSerializer
from .filters import ProductFilter


class ProductListView(ListAPIView):
    queryset = Product.objects.all().prefetch_related("sizes", "colors__images").filter(is_deleted=False)
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter

    search_fields = ["name", "brand", "category"]

    def get_queryset(self):
        queryset = super().get_queryset()

        # sorting
        sort = self.request.query_params.get("sort")
        if sort == "low-to-high":
            queryset = queryset.order_by("price")
        elif sort == "high-to-low":
            queryset = queryset.order_by("-price")

        # limit
        limit = self.request.query_params.get("_limit")
        if limit:
            try:
                queryset = queryset[: int(limit)]
            except ValueError:
                pass

        return queryset


class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.all().prefetch_related("sizes", "colors__images").filter(is_deleted=False)
    serializer_class = ProductSerializer
    lookup_field = "id"