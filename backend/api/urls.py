from django.urls import include, path
from rest_framework import routers
from api.views import (
    CustomUserMeViewSet,
    IngredientListDetailViewSet,
    TagViewSet,
    RecipeViewSet,
)

router_v1 = routers.DefaultRouter()
router_v1.register("users", CustomUserMeViewSet, basename="users")
router_v1.register("ingredients", IngredientListDetailViewSet, basename="ingredients")
router_v1.register("tags", TagViewSet, basename="tags")
router_v1.register("recipes", RecipeViewSet, basename="recipes")


urlpatterns = [
    path("", include(router_v1.urls)),
    # path("", include("djoser.urls")),
    # path("users", CustomUserMeViewSet, basename="users"),
    path("auth/", include("djoser.urls.authtoken")),
]
