import json
from products.models import Product, ProductSize, ProductColor, ProductImage

with open("products.json", "r", encoding="utf-8") as f:
    data = json.load(f)

products = data.get("products", [])

for item in products:
    product = Product.objects.create(
        name=item.get("name", ""),
        brand=item.get("brand", ""),
        price=item.get("price", 0),
        discount=item.get("discount", 0),
        description=item.get("description", ""),
        ratings=item.get("ratings", 0),
        reviews_count=item.get("reviewsCount", 0),
        category=item.get("category", "")
    )

    # Sizes
    for s in item.get("sizes", []):
        if isinstance(s, dict):
            size = s.get("size")
            stock = s.get("stock", 0)
        else:
            size = s
            stock = 10

        if size is not None:
            ProductSize.objects.create(
                product=product,
                size=size,
                stock=stock
            )

    # Colors
    for c in item.get("colors", []):
        color = ProductColor.objects.create(
            product=product,
            color_name=c.get("colorName") or c.get("name") or "Default",
            hex=c.get("hex", "#000000")
        )

        for img in c.get("images", []):
            ProductImage.objects.create(
                color=color,
                image=img
            )

print("✅ Done")