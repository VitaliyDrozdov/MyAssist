from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewset
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, filters
from api.serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeSerializer,
    RecipeIngredientSerializer,
    RecipeCreateUpdateDeleteSerializer,
    FavoritesSerializer,
)
from recipe.models import Ingredient, Tag, Recipe, Favorite
from rest_framework.pagination import LimitOffsetPagination
from api.pagination import RecipesPagination
from rest_framework.permissions import SAFE_METHODS

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
    filter_backends = (filters.OrderingFilter,)
    ordering = ("-pub_date",)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateDeleteSerializer

    @action(detail=True, methods=["post", "delete"], url_path="favorite")
    def favorite(self, request, pk: int):
        recipe = get_object_or_404(Recipe, id=pk)
        # cur_favorite = Favorite.objects.filter(user=request.user, id=pk)
        if request.method == "POST":
            Favorite.objects.create(recipe=recipe, user=request.user)
            serializer = FavoritesSerializer(recipe, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        if request.method == "DELETE":
            Favorite.objects.filter(recipe=recipe, user=request.user).delete()

    # def perform_create(self, serializer):
    #     serializer.save(author=self.request.user)
