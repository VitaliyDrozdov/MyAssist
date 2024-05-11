from django_filters import rest_framework as filters
from recipe.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(
        field_name="favorites__user", method="filter_is_favorited"
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name="shopping_cart__user", method="filter_is_in_shopping_cart"
    )

    tags = filters.ModelMultipleChoiceFilter(
        field_name="tags__slug", to_field_name="slug", queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]

    def filter_is_favorited(self, queryset: Recipe, name, value: bool):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset: Recipe, name, value: bool):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
