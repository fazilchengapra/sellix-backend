from rest_framework import serializers
from orders.models import Order, OrderItem


class OrderItemSummarySerializer(serializers.Serializer):
    """Only exposes id — frontend just needs the count."""

    id = serializers.IntegerField()


class OrderListSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    userId = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(
        source="created_at", format="%Y-%m-%dT%H:%M:%SZ"
    )
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    items = OrderItemSummarySerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "userId", "createdAt", "status", "total", "items"]

    def get_id(self, obj):
        return f"ORD-{obj.id}"

    def get_userId(self, obj):
        return str(obj.user.id)


class OrderItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product_name", "image", "size", "color", "quantity", "price"]


class OrderDetailSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    user = serializers.IntegerField(source="user.id")
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    deliveredAt = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    items = OrderItemDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "created_at",
            "deliveredAt",
            "payment_method",
            "card_name",
            "subtotal",
            "total",
            "items",
        ]

    def get_id(self, obj):
        return f"ORD-{obj.id}"

    def get_deliveredAt(self, obj):
        # Only meaningful once the order is delivered
        if obj.status == "Delivered":
            # If you add a delivered_at DateTimeField to the model later,
            # swap this line to: return obj.delivered_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            return obj.created_at.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )  # placeholder until field exists
        return None
