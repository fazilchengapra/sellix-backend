# filters.py

import django_filters
from products.models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(lookup_expr="iexact")
    brand = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Product
        fields = ["category", "brand"]
