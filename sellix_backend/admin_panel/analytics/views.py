from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from rest_framework.views import APIView
from rest_framework.response import Response
from orders.models import Order, OrderItem
import decimal
from django.db.models.functions import TruncDate


class SalesAnalyticsView(APIView):
    def get(self, request):
        total_orders = Order.objects.count()

        items_subtotal = OrderItem.objects.aggregate(
            subtotal=Sum(
                ExpressionWrapper(
                    F("price") * F("quantity"),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )
        )["subtotal"] or decimal.Decimal("0")

        total_shipping = Order.objects.aggregate(shipping=Sum("shipping"))[
            "shipping"
        ] or decimal.Decimal("0")

        total_revenue = items_subtotal + total_shipping
        avg_order_value = (
            round(total_revenue / total_orders, 2)
            if total_orders > 0
            else decimal.Decimal("0")
        )

        return Response(
            {
                "totalRevenue": float(total_revenue),
                "totalOrders": total_orders,
                "avgOrderValue": float(avg_order_value),
            }
        )


class RevenueTrendView(APIView):
    def get(self, request):
        trends = (
            OrderItem.objects.annotate(date=TruncDate("order__created_at"))
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

        # Add shipping per date
        shipping_by_date = (
            Order.objects.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(shipping=Sum("shipping"))
        )
        shipping_map = {s["date"]: s["shipping"] for s in shipping_by_date}

        data = [
            {
                "date": entry["date"].strftime("%b %d"),
                "revenue": float(
                    (entry["revenue"] or decimal.Decimal("0"))
                    + (shipping_map.get(entry["date"]) or decimal.Decimal("0"))
                ),
            }
            for entry in trends
        ]

        return Response(data)