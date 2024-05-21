from django.contrib.auth import get_user_model

from django.db.models import Sum
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import SAFE_METHODS, AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_204_NO_CONTENT,
)

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
    """ViewSet для получение списка ингредиентов или одного ингредиента по id.
    Возможен поиск по имени.
    """

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = (IngredientFilter,)
    search_fields = ("^name",)
    permission_classes = (AllowAny,)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для получение списка тэгов или одного тэга по id."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов.
    Создание, редактирование, получение списка по фильтрам,
    добавление/удаление в избранное и список покупок.
    Отправка текстового файла со списком покупок.
    """

    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    pagination_class = LimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateDeleteSerializer

    def __add__recipe(self, request, pk: int, serializer_class) -> Response:
        """Добавление рецептов в список покупок | избранное.
        Args:
            request: Request.
            pk (int): id рецепта.
            serializer_class (Serializer): тип сериализатора.
        Returns:
            Response: статус рецепта.
        """
        try:
            recipe = get_object_or_404(Recipe, id=pk)
        except Http404:
            return Response(status=HTTP_400_BAD_REQUEST)
        serializer = serializer_class(
            data={"user": request.user.id, "recipe": recipe.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def __delete_recipe(self, request, pk: int, related_name: str):
        """Удаление рецептов из списка покупок | избранного.
        Args:
            request: Request.
            pk (int): id рецепта.
            related_name (str): related_name для модели.
        Returns:
            Response: статус рецепта.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        cur_recipe_deleted, _ = (
            getattr(request.user, related_name).filter(recipe=recipe).delete()
        )
        return (
            Response(status=HTTP_400_BAD_REQUEST)
            if cur_recipe_deleted == 0
            else Response(status=HTTP_204_NO_CONTENT)
        )

    @action(detail=True, methods=["post"], url_path="favorite")
    def favorite(self, request, pk: int) -> Response:
        """Функция обработки списка избранного. Добавление рецептов.
        Args:
            request: Request.
            pk (int): id рецепта
        Returns: статус рецепта.
        """ """"""
        return self.__add__recipe(request, pk, FavoritesSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk: int) -> Response:
        """Функция обработки списка избранного. Удаление рецептов.
        Args:
            request: Request.
            pk (int): id рецепта
        Returns: статус рецепта.
        """ """"""
        return self.__delete_recipe(request, pk, "favorites")

    @action(detail=True, methods=["post"], url_path="shopping_cart")
    def shopping_cart(self, request, pk: int) -> Response:
        """Функция обработки списка покупок. Добавление рецептов.
        Args:
            request: Request.
            pk (int): id рецепта
        Returns: статус рецепта.
        """ """"""
        return self.__add__recipe(request, pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk: int) -> Response:
        """Функция обработки списка покупок. Удалениерецептов.
        Args:
            request: Request.
            pk (int): id рецепта
        Returns: статус рецепта.
        """ """"""
        return self.__delete_recipe(request, pk, "shopping_cart")

    @action(detail=False, methods=["get"], url_path="download_shopping_cart")
    def download_shopping_cart(self, request) -> HttpResponse:
        """Скачивает файл со списком покупок.
        Считает сумму ингредиентов в рецептах.
        Args:
            request: Request.
        Returns:
            HttpResponse: файл со списком ингредиентов в нужном формате.
        """
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
    def get_short_link(self, request, pk: int) -> Response:
        """Получение короткой ссылки для репепта.
        Args:
            request (_type_): Request.
            pk (int): id репепта.
        Returns:
            Response: url ссылка вида s/short_code.
        """
        serializer = ShortLinkSerializer(data={"pk": pk}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def redirect_to_recipe(request, short_code) -> HttpResponseRedirect:
    """При переходе по короткой ссылке перенаправляет на страницу рецепта.
    Args:
        request: Request.
        short_code (str): короткий slug для репепта.
    Returns:
        HttpResponseRedirect: полная сслыка на репепт.
    """
    link = get_object_or_404(Link, short_code=short_code)
    return redirect(link.original_link)
