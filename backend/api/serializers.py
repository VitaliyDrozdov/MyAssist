import base64
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import (
    UserCreateSerializer as DjoserCreateUS,
    UserSerializer as DjoserMeUS,
)
from rest_framework import serializers
from recipe.models import Ingredient, Tag, Recipe, RecipeIngredient
from django.db.models import F

User = get_user_model()


class CustomUserCreateSerializer(DjoserCreateUS):
    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name", "password")


class CustomUserProfileSerializer(DjoserMeUS):
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


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    # author = CustomUserProfileSerializer()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_ingredients(self, obj):
        ingredients_data = []
        recipe_ingredients = obj.recipeingredient_set.all()
        for recipe_ingredient in recipe_ingredients:
            ingredient_data = {
                "id": recipe_ingredient.ingredient.id,
                "name": recipe_ingredient.ingredient.name,
                "measurement_unit": recipe_ingredient.ingredient.measurement_unit,
                "amount": recipe_ingredient.amount,
            }
            ingredients_data.append(ingredient_data)
        return ingredients_data
