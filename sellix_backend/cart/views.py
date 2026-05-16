from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import CartItem
from products.models import Product, ProductSize, ProductColor
from .serializers import CartItemSerializer
from common.permissions import IsNormalUser


class CartView(APIView):
    permission_classes = [IsNormalUser]
    
    @extend_schema(
        request=None,
        responses=CartItemSerializer(many=True),
        tags=["Cart"],
    )
    def get(self, request):
        items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(items, many=True)

        total = sum(item.price * item.quantity for item in items)

        return Response({"items": serializer.data, "total": total}, status=200)
    
    @extend_schema(
        request=CartItemSerializer,
        responses={"message": str},
        tags=["Cart"],
    )
    def post(self, request):
        try:

            product_id = request.data.get("product_id")
            size = request.data.get("size")
            color = request.data.get("color")
            quantity = int(request.data.get("quantity", 1))

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=404)

            #  Validate size stock
            try:
                size_obj = ProductSize.objects.get(product=product, size=size)
            except ProductSize.DoesNotExist:
                return Response({"error": "Invalid size"}, status=400)

            if size_obj.stock < quantity:
                return Response({"error": "Not enough stock"}, status=400)

            #  Get image (first image of that color)
            color_obj = ProductColor.objects.filter(
                product=product, color_name=color
            ).first()
            image = None

            if color_obj and color_obj.images.exists():
                image = color_obj.images.first().image

            #  Prevent duplicate items
            item, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                size=size,
                color=color,
                defaults={
                    "product_name": product.name,
                    "price": product.final_price(),
                    "image": image,
                    "quantity": quantity,
                },
            )

            if not created:
                item.quantity += quantity

                if item.quantity > size_obj.stock:
                    return Response({"error": "Stock exceeded"}, status=400)

                item.save()

            return Response({"message": "Added to cart"}, status=201)
        except Exception as e:
            print("cart error:",str(e))
            return Response({"error": "something went wrong"}, status=500)


class CartDetailsView(APIView):
    permission_classes = [IsNormalUser]

    @extend_schema(
        request=CartItemSerializer,
        responses={"message": str},
        tags=["Cart"],
    )
    def patch(self, request, pk):

        try:
            item = CartItem.objects.get(id=pk, user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=404)

        quantity = int(request.data.get("quantity"))

        try:
            size_obj = ProductSize.objects.get(product=item.product, size=item.size)
        except ProductSize.DoesNotExist:
            return Response({"error": "Invalid size"}, status=400)

        if quantity > size_obj.stock:
            return Response({"error": "Stock exceeded"}, status=400)

        item.quantity = quantity
        item.save()

        return Response({"message": "Updated"}, status=200)

    @extend_schema(
        request=None,
        responses={"message": str},
        tags=["Cart"],
    )
    def delete(self, request, pk):
        try:
            item = CartItem.objects.get(id=pk, user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=404)
        item.delete()
        return Response({"message": "Removed"}, status=200)
