from django.urls import include, path
from rest_framework import routers
from api.views import (
    UserViewSet,
    IngredientListDetailViewSet,
    TagViewSet,
    RecipeViewSet,
)

router_v1 = routers.DefaultRouter()
router_v1.register("users", UserViewSet, basename="users")
router_v1.register("ingredients", IngredientListDetailViewSet, basename="ingredients")
router_v1.register("tags", TagViewSet, basename="tags")
router_v1.register("recipes", RecipeViewSet, basename="recipes")


urlpatterns = [
    path("", include(router_v1.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
