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


class DashboardView(APIView):
    def get(self, req):

        revenue_data = OrderItem.objects.filter(order__payment_status="Paid").aggregate(
            revenue=Sum(F("price") * F("quantity"))
        )

        revenue = revenue_data["revenue"] or 0
        orders = Order.objects.count()
        products = Product.objects.count()
        users = User.objects.count()

        data = {
            "revenue": revenue,
            "orders": orders,
            "products": products,
            "users": users,
        }

        serializer = DashboardSerializer(data)
        return Response(serializer.data)


class OrdersOverview(APIView):
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
