import base64
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    # tags = serializers.PrimaryKeyRelatedField(
    #     queryset=Tag.objects.all(), many=True, write_only=True
    # )
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    author = CustomUserProfileSerializer(read_only=True)

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


class RecipeCreateUpdateDeleteSerializer(serializers.ModelSerializer):
    # tags = TagSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    author = CustomUserProfileSerializer(read_only=True)
    # author = serializers.SlugRelatedField(
    #     slug_field="username",
    #     read_only=True,
    #     default=serializers.CurrentUserDefault(),
    # )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def add_tags_ingredients(self, obj: Recipe):
        if "tags" in self.validated_data:
            tags_data = self.validated_data.pop("tags")
            obj.tags.set(tags_data)
        if "ingredients" in self.validated_data:
            ingredients_data = self.validated_data.pop("ingredients")
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=obj,
                    ingredient=Ingredient.objects.get(id=ingredient_data["id"]),
                    amount=ingredient_data["amount"],
                )
        return obj

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        # tags_data = validated_data.pop("tags")
        # ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self.add_tags_ingredients(recipe)
        # for ingredient_data in ingredients_data:
        #     RecipeIngredient.objects.create(
        #         recipe=recipe,
        #         ingredient=Ingredient.objects.get(id=ingredient_data["id"]),
        #         amount=ingredient_data["amount"],
        #     )
        # recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.image = validated_data.get("image", instance.image)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        instance.image = validated_data.get("image", instance.image)
        instance.text = validated_data.get("text", instance.text)
        self.add_tags_ingredients(instance)
        # if "tags" in validated_data:
        #     tags_data = validated_data.pop("tags")
        #     instance.tags.set(tags_data)
        # if "ingredients" in validated_data:
        #     ingredients_data = validated_data.pop("ingredients")
        #     for ingredient_data in ingredients_data:
        #     RecipeIngredient.objects.create(
        #         recipe=instance,
        #         ingredient=Ingredient.objects.get(id=ingredient_data["id"]),
        #         amount=ingredient_data["amount"],
        #     )
        instance.save()
        return instance


class FavoritesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
