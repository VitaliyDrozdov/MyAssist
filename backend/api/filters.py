from django_filters.rest_framework import filters, FilterSet
from rest_framework.filters import SearchFilter

from recipe.models import Recipe, Tag


class IngredientFilter(SearchFilter):
    search_param = "name"


class RecipeFilter(FilterSet):
    is_favorited = filters.BooleanFilter(
        field_name="favorites__user", method="filter_is_favorited"
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name="shopping_cart__user", method="filter_is_in_shopping_cart"
    )

    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]

    def filter_is_favorited(self, queryset: Recipe, name, value: bool):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset: Recipe, name, value: bool):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
