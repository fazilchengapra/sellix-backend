# serializers.py
from rest_framework import serializers
from products.models import Product, ProductColor, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["image"]


class ProductColorSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductColor
        fields = ["images"]


class ProductListSerializer(serializers.ModelSerializer):
    colors = ProductColorSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "brand", "category", "price", "colors"]
