import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category", lookup_expr="iexact")
    brand = django_filters.CharFilter(field_name="brand", lookup_expr="iexact")

    class Meta:
        model = Product
        fields = ["category", "brand"]