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
from django.db.models import Q
from drf_spectacular.utils import extend_schema


class ProductListView(APIView):
    @extend_schema(
        request=None,
        responses=ProductSerializer(many=True),
        tags=["Products"],
    )
    def get(self, request):
        queryset = Product.objects.prefetch_related("sizes", "colors__images").filter(
            is_deleted=False
        )

        # Apply filters (ProductFilter)
        filterset = ProductFilter(request.GET, queryset=queryset)
        if filterset.is_valid():
            queryset = filterset.qs

        # Apply search (name, brand, category)
        search_query = request.query_params.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(brand__icontains=search_query)
                | Q(category__icontains=search_query)
            )

        # Apply sorting
        sort = request.query_params.get("sort")
        if sort == "low-to-high":
            queryset = queryset.order_by("price")
        elif sort == "high-to-low":
            queryset = queryset.order_by("-price")

        # Apply limit
        limit = request.query_params.get("_limit")
        if limit:
            try:
                queryset = queryset[: int(limit)]
            except ValueError:
                pass

        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)


class ProductDetailView(APIView):
    @extend_schema(
        request=None,
        responses=ProductSerializer,
        tags=["Products"],
    )
    def get(self, request, id):
        try:
            product = Product.objects.prefetch_related("sizes", "colors__images").get(
                id=id, is_deleted=False
            )
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
