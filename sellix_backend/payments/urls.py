from django.urls import path
from .views import InitiatePaymentView, VerifyPaymentView, RazorpayWebhookView

urlpatterns = [
    path("initiate/", InitiatePaymentView.as_view()),
    path("verify/", VerifyPaymentView.as_view()),
    path("webhook/", RazorpayWebhookView.as_view()),
]
