from rest_framework.views import APIView
from rest_framework.response import Response
from orders.models import Order, OrderItem
from django.db.models import F
from products.models import Product
from users.models import CustomUser as User
from .serializers import DashboardSerializer
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
from django.db.models import Count
from django.db.models import ExpressionWrapper, DecimalField
from rest_framework import status
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from common.permissions import IsAdminUser


class DashboardView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=None,
        responses=DashboardSerializer,
        tags=["Admin Dashboard"],
    )
    def get(self, req):

        # --- Summary Stats ---
        revenue_data = OrderItem.objects.filter(order__payment_status="Paid").aggregate(
            revenue=Sum(F("price") * F("quantity"))
        )
        data = {
            "revenue": revenue_data["revenue"] or 0,
            "orders": Order.objects.count(),
            "products": Product.objects.count(),
            "users": User.objects.filter(
                is_active=True, is_deleted=False, is_staff=False
            ).count(),
        }
        summary = DashboardSerializer(data).data

        # --- Top 5 Customers ---
        top_customers = (
            User.objects.filter(role="customer", is_active=True, is_deleted=False)
            .annotate(
                totalOrders=Count("orders", distinct=True),
                totalSpent=Sum(
                    ExpressionWrapper(
                        F("order_items__price") * F("order_items__quantity"),
                        output_field=DecimalField(),
                    ),
                    filter=Q(orders__payment_status="Paid"),
                ),
            )
            .filter(totalOrders__gt=0)
            .order_by("-totalSpent")[:5]
            .values("id", "name", "email", "totalOrders", "totalSpent")
        )

        # --- Recent 5 Orders ---
        recent_orders = (
            Order.objects.annotate(
                total=Sum(
                    ExpressionWrapper(
                        F("items__price") * F("items__quantity"),
                        output_field=DecimalField(),
                    )
                )
            )
            .order_by("-created_at")[:5]
            .values("id", "total", "created_at", "status")
        )

        return Response(
            {
                "summary": summary,
                "topCustomers": [
                    {
                        "id": u["id"],
                        "name": u["name"],
                        "email": u["email"],
                        "totalOrders": u["totalOrders"],
                        "totalSpent": float(u["totalSpent"] or 0),
                    }
                    for u in top_customers
                ],
                "recentOrders": [
                    {
                        "id": o["id"],
                        "total": float(o["total"] or 0),
                        "createdAt": o["created_at"],
                        "status": o["status"],
                    }
                    for o in recent_orders
                ],
            }
        )


class OrdersOverview(APIView):
    permission_classes = [IsAdminUser]
    @extend_schema(
        request=None,
        responses={
            200: {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "revenue": {"type": "number"},
                        "orders": {"type": "integer"},
                    },
                },
            }
        },
        tags=["Admin Dashboard"],
    )
    def get(self, request):
        days = int(request.query_params.get("days", 7))

        if days not in (7, 30):
            return Response(
                {"error": "Invalid filter. Use 7 or 30."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        since = timezone.now() - timedelta(days=days)

        # Aggregate revenue per day using item-level price * quantity
        daily_data = (
            Order.objects.filter(
                created_at__gte=since,
                payment_status="Paid",
            )
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                orders=Count("id", distinct=True),
                revenue=Sum(
                    ExpressionWrapper(
                        F("items__price") * F("items__quantity"),
                        output_field=DecimalField(),
                    )
                ),
            )
            .order_by("date")
        )

        # Format label based on filter
        def format_label(date, days):
            return date.strftime("%a") if days == 7 else date.strftime("%b %d")

        data = [
            {
                "date": format_label(entry["date"], days),
                "revenue": float(entry["revenue"] or 0),
                "orders": entry["orders"],
            }
            for entry in daily_data
        ]

        return Response(data)
