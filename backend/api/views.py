from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as DjoserUserViewset
from rest_framework.decorators import action
from rest_framework import viewsets, mixins, filters
from api.serializers import IngredientSerializer, TagSerializer, RecipeSerializer
from recipe.models import Ingredient, Tag, Recipe
from rest_framework.pagination import LimitOffsetPagination
from api.pagination import RecipesPagination

# Create your views here.
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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
