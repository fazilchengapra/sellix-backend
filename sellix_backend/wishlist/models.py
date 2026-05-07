from django.db import models
from django.conf import settings
from products.models import Product  # adjust import to your app
from users.models import CustomUser as User


class Wishlist(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="wishlist"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}'s wishlist"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("wishlist", "product")  # no duplicates

    def __str__(self):
        return f"{self.product} in {self.wishlist}"
