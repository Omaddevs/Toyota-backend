import django_filters

from .models import Category, Vendor


class CategoryFilter(django_filters.FilterSet):
    class Meta:
        model = Category
        fields = ("zone",)


class VendorFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category_id", lookup_expr="exact")
    district = django_filters.CharFilter(field_name="district", lookup_expr="icontains")
    min_rating = django_filters.NumberFilter(field_name="rating", lookup_expr="gte")
    max_rating = django_filters.NumberFilter(field_name="rating", lookup_expr="lte")

    class Meta:
        model = Vendor
        fields = ("category", "district", "min_rating", "max_rating")
