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
    ProductUpdateSerializer,
)
from common.pagination import CommonPagination
from .filters import ProductFilter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
import json
from drf_spectacular.utils import extend_schema
from common.permissions import IsAdminUser
from django.db.models import Q

# import cloudinary
# import cloudinary.uploader


class ProductListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=None,
        responses=ProductListSerializer(many=True),
        tags=["Admin Products"],
    )
    def get(self, request):
        queryset = Product.objects.prefetch_related("colors__images", "sizes").filter(
            is_deleted=False
        )

        # Apply filters (ProductFilter)
        filterset = ProductFilter(request.GET, queryset=queryset)
        if filterset.is_valid():
            queryset = filterset.qs

        # Apply search (name, brand, category)
        search_query = request.query_params.get("search", None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(brand__icontains=search_query)
                | Q(category__icontains=search_query)
            )

        # Apply ordering (price, ratings, reviews_count, id)
        ordering = request.query_params.get("ordering", "-id")
        allowed_ordering_fields = {
            "price",
            "ratings",
            "reviews_count",
            "id",
            "-price",
            "-ratings",
            "-reviews_count",
            "-id",
        }
        if ordering in allowed_ordering_fields:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by("-id")

        # Apply pagination
        paginator = CommonPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = ProductListSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProductCreateView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=ProductCreateSerializer,
        responses=ProductDetailSerializer,
        tags=["Admin Products"],
    )
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
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return Product.objects.prefetch_related("colors__images", "sizes").get(
                pk=pk, is_deleted=False
            )
        except Product.DoesNotExist:
            return None

    @extend_schema(
        request=ProductDetailSerializer,
        responses=ProductDetailSerializer,
        tags=["Admin Products"],
    )
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


class ProductDeleteView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=None,
        responses=None,
        tags=["Admin Products"],
    )
    def delete(self, request, pk):

        try:
            product = Product.objects.get(pk=pk, is_deleted=False)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND
            )
        if not product:
            return Response(
                {"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND
            )

        product.is_deleted = True
        product.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
