from django.contrib.auth import get_user_model

from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import SAFE_METHODS, AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST


from api.filters import IngredientFilter, RecipeFilter
from api.pagination import LimitPagination
from api.permissions import IsAuthorAdminOrReadOnly
from api.serializers import (
    FavoritesSerializer,
    IngredientSerializer,
    RecipeCreateUpdateDeleteSerializer,
    RecipeIngredient,
    RecipeSerializer,
    ShoppingCartSerializer,
    ShortLinkSerializer,
    TagSerializer,
)
from recipe.models import Ingredient, Link, Recipe, Tag

User = get_user_model()


class IngredientListDetailViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = (IngredientFilter,)
    search_fields = ("^name",)
    permission_classes = (AllowAny,)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    pagination_class = LimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorAdminOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateDeleteSerializer

    @action(detail=True, methods=["post", "delete"], url_path="favorite")
    def favorite(self, request, pk: int):
        try:
            recipe = get_object_or_404(Recipe, id=pk)
        except Http404:
            return Response(status=HTTP_400_BAD_REQUEST)
        if request.method == "POST":
            serializer = FavoritesSerializer(
                data={"user": request.user.id, "recipe": recipe.id},
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            cur_recipe = request.user.favorites.filter(recipe=recipe, user=request.user)
            if not cur_recipe.exists():
                return Response(status=HTTP_400_BAD_REQUEST)
            cur_recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], url_path="shopping_cart")
    def shopping_cart(self, request, pk: int):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == "POST":
            serializer = ShoppingCartSerializer(
                data={"user": request.user.id, "recipe": recipe.id},
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            cur_recipe = request.user.shopping_cart.filter(
                recipe=recipe, user=request.user
            )
            if not cur_recipe.exists():
                return Response(status=HTTP_400_BAD_REQUEST)
            cur_recipe.delete()
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

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_short_link(self, request, pk: int):
        serializer = ShortLinkSerializer(data={"pk": pk}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def redirect_to_recipe(request, short_code):
    link = get_object_or_404(Link, short_code=short_code)
    return redirect(link.original_link)
