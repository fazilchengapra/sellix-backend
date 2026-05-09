from rest_framework import serializers
from .models import RazorpayPayment


class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()


class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_order_id  = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature  = serializers.CharField()


class PaymentDetailSerializer(serializers.ModelSerializer):
    amount_in_rupees = serializers.ReadOnlyField()
    order_status = serializers.CharField(source="order.status", read_only=True)

    class Meta:
        model = RazorpayPayment
        exclude = ["raw_webhook_payload", "razorpay_signature"]