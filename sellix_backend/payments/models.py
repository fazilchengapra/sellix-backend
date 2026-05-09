import hmac
import hashlib
from django.db import models
from orders.models import Order


class RazorpayPayment(models.Model):
    STATUS_CHOICES = [
        ('created', 'Created'),        # Razorpay order created, payment not yet attempted
        ('attempted', 'Attempted'),    # Payment attempted but not captured
        ('paid', 'Paid'),              # Payment successful & verified
        ('failed', 'Failed'),          # Payment failed
        ('refunded', 'Refunded'),      # Full refund issued
        ('partially_refunded', 'Partially Refunded'),
    ]

    # --- Link to your Order ---
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,   # Never delete payments accidentally
        related_name='razorpay_payment'
    )

    # --- Razorpay IDs ---
    razorpay_order_id = models.CharField(max_length=100, unique=True)       # order_XXXXXXXXXX
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True, unique=True)  # pay_XXXXXXXXXX
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    # --- Amount (always store in paise for Razorpay, rupees for display) ---
    amount = models.PositiveIntegerField(help_text="Amount in paise (₹1 = 100 paise)")
    amount_refunded = models.PositiveIntegerField(default=0, help_text="Refunded amount in paise")
    currency = models.CharField(max_length=10, default='INR')

    # --- Status & Method ---
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='created')
    method = models.CharField(max_length=50, blank=True, null=True)  # card, upi, netbanking, wallet

    # --- Card details (only populated for card payments) ---
    card_id = models.CharField(max_length=100, blank=True, null=True)
    card_network = models.CharField(max_length=50, blank=True, null=True)   # Visa, Mastercard, etc.
    card_issuer = models.CharField(max_length=100, blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_type = models.CharField(max_length=20, blank=True, null=True)      # credit / debit

    # --- UPI details ---
    upi_transaction_id = models.CharField(max_length=100, blank=True, null=True)

    # --- Fees & Tax (from Razorpay webhook) ---
    fee = models.PositiveIntegerField(default=0, help_text="Razorpay fee in paise")
    tax = models.PositiveIntegerField(default=0, help_text="GST on Razorpay fee in paise")

    # --- Customer / Contact info at time of payment ---
    email = models.EmailField(blank=True, null=True)
    contact = models.CharField(max_length=20, blank=True, null=True)

    # --- Error info (for failed payments) ---
    error_code = models.CharField(max_length=100, blank=True, null=True)
    error_description = models.CharField(max_length=255, blank=True, null=True)
    error_source = models.CharField(max_length=100, blank=True, null=True)   # customer / bank / business
    error_step = models.CharField(max_length=100, blank=True, null=True)
    error_reason = models.CharField(max_length=100, blank=True, null=True)

    # --- Webhook / raw payload (very useful for debugging) ---
    raw_webhook_payload = models.JSONField(blank=True, null=True)

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)   # Set when status → paid

    class Meta:
        verbose_name = "Razorpay Payment"
        verbose_name_plural = "Razorpay Payments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['razorpay_payment_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.razorpay_payment_id or self.razorpay_order_id} — {self.status}"

    # --- Signature Verification ---
    def verify_signature(self, secret: str) -> bool:
        """
        Verify Razorpay webhook/payment signature.
        Call this before marking a payment as paid.
        """
        if not self.razorpay_payment_id or not self.razorpay_signature:
            return False
        body = f"{self.razorpay_order_id}|{self.razorpay_payment_id}"
        expected = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, self.razorpay_signature)

    # --- Convenience properties ---
    @property
    def amount_in_rupees(self):
        return self.amount / 100

    @property
    def refunded_in_rupees(self):
        return self.amount_refunded / 100

    @property
    def is_paid(self):
        return self.status == 'paid'