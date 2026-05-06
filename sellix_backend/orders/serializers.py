from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'price',
            'image',
            'quantity',
            'size',
            'color',
        ]
        read_only_fields = [
            'id',
            'product',
            'product_name',
            'price',
            'image',
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'items',
            'subtotal',
            'total',
            'shipping',
            'status',
            'payment_method',
            'card_name',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'items',
            'subtotal',
            'total',
            'status',
            'created_at',
        ]

    def get_subtotal(self, obj):
        return int(obj.subtotal)

    def get_total(self, obj):
        return int(obj.total)