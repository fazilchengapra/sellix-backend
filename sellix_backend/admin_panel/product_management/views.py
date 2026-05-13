from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from rest_framework.response import Response

from products.models import Product, ProductImage
from .serializers import (
    ProductCreateSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductUpdateSerializer
)
from .pagination import ProductPagination
from .filters import ProductFilter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
import json

# import cloudinary
# import cloudinary.uploader


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


class ProductCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    # def get(self, request):
    #     products = Product.objects.prefetch_related("colors__images", "sizes").all()
    #     serializer = ProductListSerializer(products, many=True)
    #     return Response(serializer.data)

    def post(self, request):
        serializer = ProductCreateSerializer(
            data=request.data,
            context={
                "request": request
            },  # ← needed to read request.FILES inside serializer
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.save()

        return Response(
            ProductDetailSerializer(product).data,
            status=status.HTTP_201_CREATED,
        )


class ProductUpdateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return Product.objects.prefetch_related("colors__images", "sizes").get(
                pk=pk
            )
        except Product.DoesNotExist:
            return None

    def patch(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response(
                {"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductUpdateSerializer(
            product,
            data=request.data,
            partial=True,  # all fields optional
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.save()

        return Response(
            ProductDetailSerializer(product).data,
            status=status.HTTP_200_OK,
        )
