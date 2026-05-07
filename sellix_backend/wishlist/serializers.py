from rest_framework import serializers
from .models import Wishlist, WishlistItem
from products.serializers import ProductSerializer  # adjust
from products.models import Product


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "product_id", "added_at"]


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "items", "created_at"]
