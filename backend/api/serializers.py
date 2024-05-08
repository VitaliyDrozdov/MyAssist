from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer as DjoserCreateUS,
    UserSerializer as DjoserMeUS,
)
from rest_framework import serializers
from recipe.models import Ingredient

User = get_user_model()


class CustomUserCreateSerializer(DjoserCreateUS):
    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name", "password")


class CustomUserMeSerializer(DjoserMeUS):
    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
