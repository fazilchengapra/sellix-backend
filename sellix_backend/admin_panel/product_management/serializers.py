import json
import re
import cloudinary.uploader
from rest_framework import serializers
from products.models import Product, ProductColor, ProductImage, ProductSize

# ─────────────────────────── Read serializers ───────────────────────────


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


class ProductColorReadSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductColor
        fields = ["id", "color_name", "hex", "images"]


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ["size", "stock"]


class ProductListSerializer(serializers.ModelSerializer):
    colors = ProductColorReadSerializer(many=True, read_only=True)
    sizes = ProductSizeSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "brand", "category", "price", "discount", "colors", "sizes"]


class ProductDetailSerializer(serializers.ModelSerializer):
    colors = ProductColorReadSerializer(many=True, read_only=True)
    sizes = ProductSizeSerializer(many=True, read_only=True)
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "brand",
            "category",
            "price",
            "discount",
            "final_price",
            "description",
            "ratings",
            "reviews_count",
            "colors",
            "sizes",
        ]

    def get_final_price(self, obj):
        return obj.final_price()


# ─────────────────────────── Write serializer ───────────────────────────


class ProductCreateSerializer(serializers.ModelSerializer):
    """
    Accepts multipart/form-data matching exactly what the frontend sends:

        name           → "Hello"
        brand          → "Nike"
        category       → "sports"
        price          → 1000
        discount       → 5
        description    → "..."
        sizes          → '[{"size": 40, "stock": 10}]'          (JSON string)
        colors         → '[{"id":null,"color_name":"Black","hex":"#000000","existing_images":[]}]'
        color_0_images → <File>   (files for first color)
        color_1_images → <File>   (files for second color)
        ...
    """

    # Accept as plain strings; we parse + validate them manually
    sizes = serializers.CharField(required=False, default="[]")
    colors = serializers.CharField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "brand",
            "price",
            "discount",
            "description",
            "category",
            "sizes",
            "colors",
        ]
        read_only_fields = ["id"]

    # ── Field-level validation ───────────────────────────────────────

    def validate_sizes(self, value):
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            raise serializers.ValidationError("sizes must be a valid JSON string.")

        if not isinstance(data, list):
            raise serializers.ValidationError("sizes must be a list.")

        seen = set()
        for item in data:
            if not isinstance(item, dict) or "size" not in item or "stock" not in item:
                raise serializers.ValidationError(
                    "Each size entry must have 'size' and 'stock'."
                )
            if not isinstance(item["size"], int) or item["size"] <= 0:
                raise serializers.ValidationError("size must be a positive integer.")
            if not isinstance(item["stock"], int) or item["stock"] < 0:
                raise serializers.ValidationError(
                    "stock must be a non-negative integer."
                )
            if item["size"] in seen:
                raise serializers.ValidationError(f"Duplicate size {item['size']}.")
            seen.add(item["size"])

        return data  # return parsed list, not raw string

    def validate_colors(self, value):
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            raise serializers.ValidationError("colors must be a valid JSON string.")

        if not isinstance(data, list) or len(data) == 0:
            raise serializers.ValidationError("colors must be a non-empty list.")

        hex_re = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
        seen_names, seen_hex = set(), set()

        for item in data:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Each color entry must be an object.")
            for field in ("color_name", "hex"):
                if field not in item:
                    raise serializers.ValidationError(
                        f"Each color entry must contain '{field}'."
                    )

            name = item["color_name"].strip()
            hex_val = item["hex"].strip()

            if not name:
                raise serializers.ValidationError("color_name cannot be empty.")
            if not hex_re.match(hex_val):
                raise serializers.ValidationError(
                    f"'{hex_val}' is not a valid hex color."
                )
            if name.lower() in seen_names:
                raise serializers.ValidationError(f"Duplicate color name '{name}'.")
            if hex_val.lower() in seen_hex:
                raise serializers.ValidationError(f"Duplicate hex '{hex_val}'.")

            seen_names.add(name.lower())
            seen_hex.add(hex_val.lower())

        return data  # return parsed list

    # ── Create ──────────────────────────────────────────────────────

    def create(self, validated_data):
        sizes_data = validated_data.pop("sizes")
        colors_data = validated_data.pop("colors")  # already a parsed list
        request = self.context["request"]

        # 1. Create the product
        product = Product.objects.create(**validated_data)

        # 2. Bulk-create sizes (skip if none sent)
        if sizes_data:
            ProductSize.objects.bulk_create(
                [
                    ProductSize(product=product, size=s["size"], stock=s["stock"])
                    for s in sizes_data
                ]
            )

        # 3. Create colors + upload images from color_<index>_images
        for index, color_data in enumerate(colors_data):
            color = ProductColor.objects.create(
                product=product,
                color_name=color_data["color_name"].strip(),
                hex=color_data["hex"].strip(),
            )

            # Frontend sends files as: color_0_images, color_1_images, …
            files = request.FILES.getlist(f"color_{index}_images")
            self._upload_images(color, files)

        return product

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _upload_images(color: ProductColor, files: list):
        """Upload files to Cloudinary and bulk-create ProductImage records."""
        if not files:
            return

        image_objects = []
        for file in files:
            result = cloudinary.uploader.upload(
                file,
                folder="products",
                resource_type="image",
            )
            image_objects.append(ProductImage(color=color, image=result["secure_url"]))

        ProductImage.objects.bulk_create(image_objects)


class ProductUpdateSerializer(serializers.ModelSerializer):
    """
    Accepts multipart/form-data.

    Fields:
        - Any Product field you want to update (all optional)
        - sizes              : JSON string → [{"size": 40, "stock": 10}, …]  (optional)
        - colors             : JSON string → [
                                  {"id": 1,    "color_name": "Black", "hex": "#000000", "delete": false},
                                  {"id": null, "color_name": "Green", "hex": "#00FF00"}
                               ]
        - deleted_image_ids  : JSON string → [1, 2, 5]   (image IDs to delete)
        - color_<index>_images : File(s) for the color at that index in the colors list
    """

    sizes = serializers.CharField(required=False)
    colors = serializers.CharField(required=False)
    deleted_image_ids = serializers.CharField(required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "brand",
            "price",
            "discount",
            "description",
            "category",
            "sizes",
            "colors",
            "deleted_image_ids",
        ]
        read_only_fields = ["id"]
        # All fields optional for partial update
        extra_kwargs = {field: {"required": False} for field in fields}

    # ── Validation ───────────────────────────────────────────────────

    def validate_sizes(self, value):
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            raise serializers.ValidationError("sizes must be a valid JSON string.")
        if not isinstance(data, list):
            raise serializers.ValidationError("sizes must be a list.")
        for item in data:
            if "size" not in item or "stock" not in item:
                raise serializers.ValidationError(
                    "Each size entry must have 'size' and 'stock'."
                )
            if not isinstance(item["size"], int) or item["size"] <= 0:
                raise serializers.ValidationError("size must be a positive integer.")
            if not isinstance(item["stock"], int) or item["stock"] < 0:
                raise serializers.ValidationError(
                    "stock must be a non-negative integer."
                )
        return data

    def validate_colors(self, value):
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            raise serializers.ValidationError("colors must be a valid JSON string.")
        if not isinstance(data, list):
            raise serializers.ValidationError("colors must be a list.")

        hex_re = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
        for item in data:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Each color entry must be an object.")
            if "color_name" not in item or "hex" not in item:
                raise serializers.ValidationError(
                    "Each color must have 'color_name' and 'hex'."
                )
            if not hex_re.match(item["hex"].strip()):
                raise serializers.ValidationError(
                    f"'{item['hex']}' is not a valid hex color."
                )
        return data

    def validate_deleted_image_ids(self, value):
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            raise serializers.ValidationError(
                "deleted_image_ids must be a valid JSON string."
            )
        if not isinstance(data, list):
            raise serializers.ValidationError("deleted_image_ids must be a list.")
        if not all(isinstance(i, int) for i in data):
            raise serializers.ValidationError("All image IDs must be integers.")
        return data

    # ── Update ───────────────────────────────────────────────────────

    def update(self, instance, validated_data):
        sizes_data = validated_data.pop("sizes", None)
        colors_data = validated_data.pop("colors", None)
        deleted_image_ids = validated_data.pop("deleted_image_ids", [])
        request = self.context["request"]

        # 1. Update basic product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 2. Update sizes — replace all existing with new list if provided
        if sizes_data is not None:
            instance.sizes.all().delete()
            ProductSize.objects.bulk_create(
                [
                    ProductSize(product=instance, size=s["size"], stock=s["stock"])
                    for s in sizes_data
                ]
            )

        # 3. Delete images explicitly marked for deletion
        if deleted_image_ids:
            ProductImage.objects.filter(
                id__in=deleted_image_ids,
                color__product=instance,  # security: only this product's images
            ).delete()

        # 4. Process colors
        if colors_data is not None:
            for index, color_data in enumerate(colors_data):
                color_id = color_data.get("id")
                should_delete = color_data.get("delete", False)

                if color_id and should_delete:
                    # Delete existing color + its images
                    ProductColor.objects.filter(id=color_id, product=instance).delete()

                elif color_id:
                    # Update existing color
                    ProductColor.objects.filter(id=color_id, product=instance).update(
                        color_name=color_data["color_name"].strip(),
                        hex=color_data["hex"].strip(),
                    )
                    color = ProductColor.objects.get(id=color_id)

                    # Upload any new images for this color
                    files = request.FILES.getlist(f"color_{index}_images")
                    self._upload_images(color, files)

                else:
                    # Create new color
                    color = ProductColor.objects.create(
                        product=instance,
                        color_name=color_data["color_name"].strip(),
                        hex=color_data["hex"].strip(),
                    )
                    files = request.FILES.getlist(f"color_{index}_images")
                    self._upload_images(color, files)

        return instance

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _upload_images(color: ProductColor, files: list):
        if not files:
            return
        image_objects = []
        for file in files:
            result = cloudinary.uploader.upload(
                file,
                folder="products",
                resource_type="image",
            )
            image_objects.append(ProductImage(color=color, image=result["secure_url"]))
        ProductImage.objects.bulk_create(image_objects)
