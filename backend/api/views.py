from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewset
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, filters
from django_filters.rest_framework import DjangoFilterBackend
from api.serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeSerializer,
    RecipeCreateUpdateDeleteSerializer,
    FavoritesShoppingCartSerializer,
    RecipeIngredient,
)
from recipe.models import Ingredient, Tag, Recipe, Favorite, ShoppingCart
from rest_framework.pagination import LimitOffsetPagination
from api.pagination import RecipesPagination
from rest_framework.permissions import SAFE_METHODS
from rest_framework import status
from api.filters import RecipeFilter
from django.db.models import Sum
from django.http import HttpResponse

User = get_user_model()


class CustomUserMeViewSet(DjoserUserViewset):

    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)


class IngredientListDetailViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ("^name",)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    pagination_class = RecipesPagination
    # filter_backends = (filters.OrderingFilter,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    # ordering = ("-pub_date",)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateDeleteSerializer

    @action(detail=True, methods=["post", "delete"], url_path="favorite")
    def favorite(self, request, pk: int):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == "POST":
            Favorite.objects.create(recipe=recipe, user=request.user)
            serializer = FavoritesShoppingCartSerializer(recipe)
            return Response(serializer.data)
        elif request.method == "DELETE":
            Favorite.objects.filter(recipe=recipe, user=request.user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], url_path="shopping_cart")
    def shopping_cart(self, request, pk: int):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == "POST":
            ShoppingCart.objects.create(recipe=recipe, user=request.user)
            serializer = FavoritesShoppingCartSerializer(recipe)
            return Response(serializer.data)
        elif request.method == "DELETE":
            ShoppingCart.objects.filter(recipe=recipe, user=request.user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="download_shopping_cart")
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            RecipeIngredient.objects.filter(recipe__shopping_cart__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(amount=Sum("amount"))
        )
        shopping_list = "Список покупок\n"
        for ingredient in ingredients:
            shopping_list += "".join(
                f'- {ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measurement_unit"]})'
                f' - {ingredient["amount"]}\n'
            )

        filename = f"{user.username}_shopping_list.txt"
        response = HttpResponse(shopping_list, content_type="text/plain")
        response["Content-Disposition"] = f"attachment; filename={filename}.txt"

        return response
