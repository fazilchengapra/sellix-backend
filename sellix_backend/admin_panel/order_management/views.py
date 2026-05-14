from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status

from users.models import CustomUser as User
from orders.models import Order
from .serializers import OrderListSerializer, OrderDetailSerializer
from common.pagination import CommonPagination
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from common.permissions import IsAdminUser


def get_order_or_404(pk):
    try:
        return Order.objects.select_related("user").prefetch_related("items").get(pk=pk)
    except Order.DoesNotExist:
        raise NotFound(detail=f"Order with id {pk} not found.")


class AdminOrderListView(APIView):
    permission_classes = [IsAdminUser]
    @extend_schema(
        request=None,
        responses=OrderListSerializer(many=True),
        tags=["Admin Orders"],
    )
    def get(self, request):
        orders = (
            Order.objects.select_related("user")
            .prefetch_related("items")
            .order_by("-created_at")
            .filter(is_deleted=False)
        )
        
        search = request.query_params.get('search', '')
        if search:
            orders = orders.filter(
                Q(user__name__icontains=search) |
                Q(user__id__icontains=search) |
                Q(user__email__icontains=search) |
                Q(id__icontains=search)
            )
            
        filter_status = request.query_params.get('status')
        if filter_status:
            valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
            if filter_status not in valid_statuses:
                return Response(
                    {"error": "Invalid status filter"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            orders = orders.filter(status=filter_status)
        
        pagenator = CommonPagination()
        paginated_orders = pagenator.paginate_queryset(orders, request)
        serializer = OrderListSerializer(paginated_orders, many=True)
        return pagenator.get_paginated_response(serializer.data)


class AdminOrderDetailView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=None,
        responses=OrderDetailSerializer,
        tags=["Admin Orders"],
    )
    def get(self, request, pk):
        return Response(
            OrderDetailSerializer(get_order_or_404(pk)).data
        )
        
    @extend_schema(
        request=OrderDetailSerializer,
        responses=OrderDetailSerializer,
        operation_id="AdminUpdateOrder",
        tags=["Admin Orders"],
    )
    def patch(self, request, pk):
        if request.data == {}:
            return Response(
                {"error": "No data provided for update."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = get_order_or_404(pk)

        ALLOWED_FIELDS = {"status", "payment_status"}
        data = {k: v for k, v in request.data.items() if k in ALLOWED_FIELDS}

        if not data:
            return Response(
                {"error": f"Only these fields are updatable: {ALLOWED_FIELDS}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status in ["Delivered", "Cancelled"]:
            return Response(
                {
                    "error": f"Cannot update status of an order that is already {order.status}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "status" in data:
            valid = [s[0] for s in Order.STATUS_CHOICES]
            if data["status"] not in valid:
                return Response(
                    {"error": f"Invalid status"}, status=status.HTTP_400_BAD_REQUEST
                )

        if "payment_status" in data:
            valid = [s[0] for s in Order.PAYMENT_STATUS_CHOICES]
            if data["payment_status"] not in valid:
                return Response(
                    {"error": f"Invalid payment_status. Choose from: {valid}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        for attr, value in data.items():
            setattr(order, attr, value)
        order.save()

        return Response(OrderDetailSerializer(order).data)
    
    @extend_schema(
        request=None,
        responses=None,
        tags=["Admin Orders"],
    )
    def delete(self, request, pk):
        order = get_order_or_404(pk)
        order.is_deleted = True
        order.save()
        return Response({"message": f"Order {pk} deleted."}, status=status.HTTP_200_OK)