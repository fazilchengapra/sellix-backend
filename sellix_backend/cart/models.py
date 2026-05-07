from django.db import models
from users.models import CustomUser
from products.models import Product
from users.models import CustomUser as User


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField()

    quantity = models.PositiveIntegerField(default=1)

    size = models.IntegerField()
    color = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("user", "product", "size", "color")