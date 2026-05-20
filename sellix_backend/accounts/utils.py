from django.core.mail import send_mail
from django.conf import settings
from cart.models import CartItem

def send_verification_email(user, token_obj):
    verify_url = f"{settings.FRONTEND_URL}/auth/verify-account/?token={token_obj.token}"

    send_mail(
        subject="Verify your account",
        message=f"Hi {user.username},\n\nClick the link below to verify your account:\n{verify_url}\n\nThis link expires in 24 hours.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

def mergeCart(user, guest_id, is_sign_up = False):
    if not guest_id or not user:
        return
    
    guest_items = CartItem.objects.filter(guest_id=guest_id)
    
    if is_sign_up:
        for guest_item in guest_items:
            guest_item.user = user
            guest_item.guest_id = None
            guest_item.save()
        return
    
    for guest_item in guest_items:
        existing_item = CartItem.objects.filter(
            user=user,
            product=guest_item.product,
            size = guest_item.size,
            color = guest_item.color
        ).first()

        if existing_item:
            existing_item.quantity += guest_item.quantity
            existing_item.save()
            guest_item.delete()

        else:
            guest_item.user = user
            guest_item.guest_id = None
            guest_item.save()