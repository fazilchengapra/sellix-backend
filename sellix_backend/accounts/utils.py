from django.core.mail import send_mail
from django.conf import settings

def send_verification_email(user, token_obj):
    verify_url = f"{settings.FRONTEND_URL}/auth/verify-account/?token={token_obj.token}"

    send_mail(
        subject="Verify your account",
        message=f"Hi {user.username},\n\nClick the link below to verify your account:\n{verify_url}\n\nThis link expires in 24 hours.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )