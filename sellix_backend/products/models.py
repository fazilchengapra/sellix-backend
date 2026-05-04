from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.PositiveIntegerField(default=0)
    description = models.TextField()
    ratings = models.FloatField(default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=100)

    def final_price(self):
        return self.price - (self.price * self.discount / 100)

    def __str__(self):
        return self.name


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size = models.IntegerField()
    stock = models.PositiveIntegerField()


class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="colors")
    color_name = models.CharField(max_length=50)
    hex = models.CharField(max_length=7)


class ProductImage(models.Model):
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name="images")
    image = models.URLField()