from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Wishlist, WishlistItem
from .serializers import WishlistSerializer, WishlistItemSerializer
from products.models import Product
from common.permissions import IsNormalUser


class WishlistView(APIView):
    permission_classes = [IsNormalUser]

    def get_wishlist(self, user):
        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        return wishlist

    def get(self, request):
        wishlist = self.get_wishlist(request.user)
        serializer = WishlistSerializer(wishlist)
        return Response(serializer.data)

    def post(self, request):
        """Add a product to wishlist"""
        wishlist = self.get_wishlist(request.user)
        product_id = request.data.get("product_id")

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist, product=product
        )
        if not created:
            return Response({"message": "Already in wishlist"}, status=200)

        return Response(WishlistItemSerializer(item).data, status=201)

class WishlistItemDeleteView(APIView):
    permission_classes = [IsNormalUser]

    def delete(self, request, item_id):
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if not wishlist:
            return Response({"error": "Wishlist not found"}, status=404)

        item = WishlistItem.objects.filter(wishlist=wishlist, id=item_id).first()
        if not item:
            return Response({"error": "Item not found in wishlist"}, status=404)

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
