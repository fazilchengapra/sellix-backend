import json, hmac, hashlib
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from .models import RazorpayPayment
from .razorpay_client import client
from .serializers import (
    InitiatePaymentSerializer,
    VerifyPaymentSerializer,
    PaymentDetailSerializer,
)


class InitiatePaymentView(APIView):
    """
    POST /payments/initiate/
    Creates a Razorpay order and stores a RazorpayPayment row.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = InitiatePaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        try:
            order = Order.objects.get(
                id=ser.validated_data["order_id"], user=request.user
            )
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=404)

        if hasattr(order, "razorpay_payment"):
            rp = order.razorpay_payment
            return Response(
                {
                    "razorpay_order_id": rp.razorpay_order_id,
                    "amount": rp.amount,
                    "currency": rp.currency,
                    "key": settings.RAZORPAY_KEY_ID,
                }
            )

        amount_paise = int(order.total * 100)

        rz_order = client.order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"order_{order.id}",
                "payment_capture": 1,  # auto-capture
            }
        )

        rp = RazorpayPayment.objects.create(
            order=order,
            razorpay_order_id=rz_order["id"],
            amount=amount_paise,
            currency="INR",
            email=request.user.email,
            contact=getattr(request.user, "phone", ""),
        )

        return Response(
            {
                "razorpay_order_id": rp.razorpay_order_id,
                "amount": rp.amount,
                "currency": rp.currency,
                "key": settings.RAZORPAY_KEY_ID,
            },
            status=201,
        )


class VerifyPaymentView(APIView):
    """
    POST /payments/verify/
    Called by frontend after Razorpay modal success callback.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = VerifyPaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        try:
            rp = RazorpayPayment.objects.select_related("order").get(
                razorpay_order_id=d["razorpay_order_id"],
                order__user=request.user,
            )
        except RazorpayPayment.DoesNotExist:
            return Response({"detail": "Payment record not found."}, status=404)

        # HMAC-SHA256 verification — never skip this
        body = f"{d['razorpay_order_id']}|{d['razorpay_payment_id']}"
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(), body.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected, d["razorpay_signature"]):
            rp.status = "failed"
            rp.error_description = "Signature mismatch"
            rp.save(update_fields=["status", "error_description"])
            return Response({"detail": "Invalid signature."}, status=400)

        # Fetch full payment details from Razorpay
        payment_data = client.payment.fetch(d["razorpay_payment_id"])

        rp.razorpay_payment_id = d["razorpay_payment_id"]
        rp.razorpay_signature = d["razorpay_signature"]
        rp.status = "paid"
        rp.method = payment_data.get("method")
        rp.fee = payment_data.get("fee", 0)
        rp.tax = payment_data.get("tax", 0)
        rp.paid_at = timezone.now()

        if payment_data.get("method") == "card":
            card = payment_data.get("card", {})
            rp.card_id = card.get("id")
            rp.card_network = card.get("network")
            rp.card_issuer = card.get("issuer")
            rp.card_last4 = card.get("last4")
            rp.card_type = card.get("type")
        elif payment_data.get("method") == "upi":
            rp.upi_transaction_id = payment_data.get("acquirer_data", {}).get(
                "upi_transaction_id"
            )

        rp.save()

        # Advance order status
        rp.order.status = "Processing"
        rp.order.save(update_fields=["status"])

        return Response(PaymentDetailSerializer(rp).data)


@method_decorator(csrf_exempt, name="dispatch")
class RazorpayWebhookView(APIView):
    """
    POST /payments/webhook/
    Async events from Razorpay (payment.captured, payment.failed, refund.created).
    Must be exempt from CSRF. Validate using webhook secret, NOT the key secret.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.body
        signature = request.headers.get("X-Razorpay-Signature", "")
        secret = settings.RAZORPAY_WEBHOOK_SECRET.encode()

        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return Response({"detail": "Invalid webhook signature."}, status=400)

        event = json.loads(payload)
        self._handle(event)
        return Response({"status": "ok"})

    def _handle(self, event):
        name = event.get("event")
        entity = event.get("payload", {}).get("payment", {}).get("entity", {})
        rz_order_id = entity.get("order_id")

        try:
            rp = RazorpayPayment.objects.select_related("order").get(
                razorpay_order_id=rz_order_id
            )
        except RazorpayPayment.DoesNotExist:
            return

        rp.raw_webhook_payload = event

        if name == "payment.captured":
            rp.status = "paid"
            rp.paid_at = timezone.now()
            rp.order.status = "Processing"
            rp.order.save(update_fields=["status"])

        elif name == "payment.failed":
            rp.status = "failed"
            rp.error_code = entity.get("error_code")
            rp.error_description = entity.get("error_description")
            rp.error_source = entity.get("error_source")
            rp.error_step = entity.get("error_step")
            rp.error_reason = entity.get("error_reason")
            rp.order.status = "Cancelled"
            rp.order.save(update_fields=["status"])

        elif name == "refund.created":
            refund = event.get("payload", {}).get("refund", {}).get("entity", {})
            rp.amount_refunded += refund.get("amount", 0)
            rp.status = (
                "refunded" if rp.amount_refunded >= rp.amount else "partially_refunded"
            )

        rp.save()
