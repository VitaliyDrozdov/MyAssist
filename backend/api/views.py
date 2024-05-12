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
    ShortLinkSerializer,
    SubscribeSerializer,
    CustomUserProfileSerializer,
)
from recipe.models import Ingredient, Tag, Recipe, Favorite, ShoppingCart
from api.pagination import LimitPagination
from rest_framework.permissions import SAFE_METHODS
from rest_framework import status
from api.filters import RecipeFilter, IngredientFilter
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.models import Subscription
from rest_framework.status import HTTP_400_BAD_REQUEST

User = get_user_model()


class UserViewSet(DjoserUserViewset):
    queryset = User.objects.all()
    serializer_class = CustomUserProfileSerializer
    pagination_class = LimitPagination
    permission_classes = (AllowAny,)

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="subscribe",
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        following = get_object_or_404(User, id=self.kwargs.get("id"))
        if request.method == "POST":
            serializer = SubscribeSerializer(
                following, data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user, following=following)
            return Response(serializer.data)
        elif request.method == "DELETE":
            Subscription.objects.filter(following=following, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        url_path="subscriptions",
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = User.objects.filter(following__user=user)
        if subscriptions:
            pages = self.paginate_queryset(subscriptions)
            serializer = SubscribeSerializer(
                pages, many=True, context={"request": request}
            )
            # serializer.is_valid(raise_exception=True)
            return self.get_paginated_response(serializer.data)
        else:
            return Response("Подписки отсутствуют", status=HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)


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

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_short_link(self, request, pk: int):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = ShortLinkSerializer(recipe)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()
        return Response(serializer.data)
