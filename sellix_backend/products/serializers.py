from rest_framework import serializers
from .models import Product, ProductSize, ProductColor, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']


class ProductColorSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)

    class Meta:
        model = ProductColor
        fields = ['color_name', 'hex', 'images']


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ['size', 'stock']


class ProductSerializer(serializers.ModelSerializer):
    sizes = ProductSizeSerializer(many=True)
    colors = ProductColorSerializer(many=True)
    finalPrice = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'brand', 'price', 'discount',
            'finalPrice', 'sizes', 'colors',
            'description', 'ratings', 'reviews_count', 'category'
        ]

    def get_finalPrice(self, obj):
        return obj.final_price()