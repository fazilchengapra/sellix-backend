from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.models import CartItem


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all orders for logged in user"""
        orders = Order.objects.filter(
            user=request.user
        ).prefetch_related('items').order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Place order from cart"""
        user = request.user

        # 1. Get cart items
        cart_items = CartItem.objects.filter(
            user=user
        ).select_related('product')

        if not cart_items.exists():
            return Response(
                {"error": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Get checkout info from request
        payment_method = request.data.get('payment_method', 'Card')
        card_name = request.data.get('card_name', '')
        shipping = request.data.get('shipping', 0)

        # 3. Validate payment method
        valid_payments = ['Card', 'UPI', 'COD']
        if payment_method not in valid_payments:
            return Response(
                {"error": f"payment_method must be one of {valid_payments}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Create order
        order = Order.objects.create(
            user=user,
            payment_method=payment_method,
            card_name=card_name,
            shipping=shipping,
        )

        # 5. Copy cart items → order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                user=user,
                product=cart_item.product,
                product_name=cart_item.product_name,
                price=cart_item.price,
                image=cart_item.image,
                size=cart_item.size,
                color=cart_item.color,
                quantity=cart_item.quantity,
            )

        # 6. Clear cart
        cart_items.delete()

        # 7. Return created order
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """Get single order"""
        order = get_object_or_404(Order, id=order_id, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def patch(self, request, order_id):
        """Update order status only"""
        order = get_object_or_404(Order, id=order_id, user=request.user)
        serializer = OrderSerializer(
            order,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, order_id):
        """Cancel order — only if Pending"""
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.status != 'Pending':
            return Response(
                {"error": "Only Pending orders can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'Cancelled'
        order.save()
        return Response(
            {"message": "Order cancelled successfully."},
            status=status.HTTP_200_OK
        )