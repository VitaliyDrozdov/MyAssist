from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as DjoserUserViewset
from rest_framework.decorators import action
from rest_framework import viewsets, mixins, filters
from api.serializers import IngredientSerializer
from recipe.models import Ingredient

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
