from django.contrib import admin
from .models import Product, ProductSize, ProductColor, ProductImage

admin.site.register(Product)
admin.site.register(ProductSize)
admin.site.register(ProductColor)
admin.site.register(ProductImage)