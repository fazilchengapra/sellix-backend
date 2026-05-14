from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from orders.models import Order, OrderItem
from datetime import timedelta
import decimal
from drf_spectacular.utils import extend_schema
from common.permissions import IsAdminUser


class SalesAnalyticsView(APIView):
    permission_classes = [IsAdminUser]
    @extend_schema(
        request=None,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "object",
                        "properties": {
                            "totalRevenue": {"type": "number"},
                            "totalOrders": {"type": "integer"},
                            "avgOrderValue": {"type": "number"},
                        },
                    },
                    "revenueTrend": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string"},
                                "revenue": {"type": "number"},
                            },
                        },
                    },
                    "salesByCategory": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "number"},
                            },
                        },
                    },
                    "orderStatus": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "integer"},
                            },
                        },
                    },
                    "topProducts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "sales": {"type": "integer"},
                                "revenue": {"type": "number"},
                            },
                        },
                    },
                },
            }
        },
        tags=["Admin Analytics"],
    )
    def get(self, request):
        days_map = {"7": 7, "30": 30, "90": 90}
        days = days_map.get(request.query_params.get("days", "30"), 30)
        start_date = timezone.now() - timedelta(days=days)

        orders = Order.objects.filter(created_at__gte=start_date)
        order_items = OrderItem.objects.filter(order__created_at__gte=start_date)

        # --- Sales Summary ---
        total_orders = orders.count()

        items_subtotal = order_items.aggregate(
            subtotal=Sum(
                ExpressionWrapper(
                    F("price") * F("quantity"),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )
        )["subtotal"] or decimal.Decimal("0")

        total_shipping = orders.aggregate(shipping=Sum("shipping"))[
            "shipping"
        ] or decimal.Decimal("0")

        total_revenue = items_subtotal + total_shipping
        avg_order_value = (
            round(total_revenue / total_orders, 2)
            if total_orders > 0
            else decimal.Decimal("0")
        )

        # --- Revenue Trend ---
        trends = (
            order_items.annotate(date=TruncDate("order__created_at"))
            .values("date")
            .annotate(
                revenue=Sum(
                    ExpressionWrapper(
                        F("price") * F("quantity"),
                        output_field=DecimalField(max_digits=10, decimal_places=2),
                    )
                )
            )
            .order_by("date")
        )

        shipping_by_date = (
            orders.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(shipping=Sum("shipping"))
        )
        shipping_map = {s["date"]: s["shipping"] for s in shipping_by_date}

        revenue_trend = [
            {
                "date": entry["date"].strftime("%b %d"),
                "revenue": float(
                    (entry["revenue"] or decimal.Decimal("0"))
                    + (shipping_map.get(entry["date"]) or decimal.Decimal("0"))
                ),
            }
            for entry in trends
        ]

        # --- Sales by Category ---
        sales_by_category = (
            order_items.values(category=F("product__category"))
            .annotate(
                value=Sum(
                    ExpressionWrapper(
                        F("price") * F("quantity"),
                        output_field=DecimalField(max_digits=10, decimal_places=2),
                    )
                )
            )
            .order_by("-value")
        )

        # --- Order Status ---
        order_status = (
            orders.values("status").annotate(value=Count("id")).order_by("-value")
        )

        # --- Top 5 Selling Products ---
        top_products = (
            order_items.values(name=F("product_name"))
            .annotate(
                sales=Sum("quantity"),
                revenue=Sum(
                    ExpressionWrapper(
                        F("price") * F("quantity"),
                        output_field=DecimalField(max_digits=10, decimal_places=2),
                    )
                ),
            )
            .order_by("-sales")[:5]
        )

        return Response(
            {
                "summary": {
                    "totalRevenue": float(total_revenue),
                    "totalOrders": total_orders,
                    "avgOrderValue": float(avg_order_value),
                },
                "revenueTrend": revenue_trend,
                "salesByCategory": [
                    {
                        "name": entry["category"] or "Uncategorized",
                        "value": float(entry["value"] or decimal.Decimal("0")),
                    }
                    for entry in sales_by_category
                ],
                "orderStatus": [
                    {
                        "name": entry["status"],
                        "value": entry["value"],
                    }
                    for entry in order_status
                ],
                "topProducts": [
                    {
                        "name": entry["name"],
                        "sales": entry["sales"] or 0,
                        "revenue": float(entry["revenue"] or decimal.Decimal("0")),
                    }
                    for entry in top_products
                ],
            }
        )
