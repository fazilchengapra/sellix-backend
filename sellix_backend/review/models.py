# reviews/models.py
from django.db import models
from users.models import CustomUser as User
from products.models import Product


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    
    rating = models.PositiveSmallIntegerField()  # 1–5
    title = models.CharField(max_length=150, blank=True)
    body = models.TextField(blank=True)
    
    is_verified_purchase = models.BooleanField(default=False)  # True if user actually ordered this product
    is_deleted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "product")  # one review per user per product
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "rating"]),
        ]

    def __str__(self):
        return f"{self.user.name} → {self.product.name} ({self.rating}★)"


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="images")
    image = models.URLField()
    order = models.PositiveSmallIntegerField(default=0)  # for ordering images in frontend

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Image for review {self.review.id}"