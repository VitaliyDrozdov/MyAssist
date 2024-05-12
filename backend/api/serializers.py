import base64
from random import randint
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from djoser.serializers import (
    UserCreateSerializer as DjoserCreateUS,
    UserSerializer as DjoserMeUS,
)
from rest_framework import serializers
from recipe.models import Ingredient, Tag, Recipe, RecipeIngredient, Link
from users.models import Subscription
from string import ascii_lowercase, ascii_uppercase, digits
from django.utils.crypto import get_random_string


User = get_user_model()


class CustomUserCreateSerializer(DjoserCreateUS):
    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name", "password")


class CustomUserProfileSerializer(DjoserMeUS):
    is_subscribed = serializers.SerializerMethodField()

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

    def get_is_subscribed(self, obj: User):
        user = self.context.get("request").user
        if user.is_anonymous or obj == user:
            return False
        return Subscription.objects.filter(user=user, following=obj).exists()


# class SubscribeSerializer(CustomUserProfileSerializer):


class SubscribeSerializer(serializers.ModelSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta(CustomUserProfileSerializer.Meta):
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )
        read_only_fields = ("email", "username", "first_name", "last_name", "avatar")

    def get_recipes_count(self, obj: Recipe):
        return obj.recipes.count()

    def get_recipes(self, obj: Recipe):
        request = self.context.get("request")
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get("recipes_limit")
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        serializer = FavoritesShoppingCartSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_is_subscribed(self, obj: User):
        user = self.context.get("request").user
        if user.is_anonymous or obj == user:
            return False
        return Subscription.objects.filter(user=user, following=obj).exists()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data: str):
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
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    author = CustomUserProfileSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def validate_ingredients(self, data):
        if not data:
            raise serializers.ValidationError(
                "Поле 'ingredients' не может быть пустым."
            )
        for ingredient in data:
            if not Ingredient.objects.filter(id=ingredient.get("id")).exists():
                raise serializers.ValidationError(f"Ингредиент не существует.")
            if ingredient.get("amount", 0) <= 0:
                raise serializers.ValidationError(
                    f"Количество должно быть больше нуля."
                )
            ingr_ids = set()
            if cur_id := ingredient.get("id") in ingr_ids:
                raise serializers.ValidationError(f"Ингредиент уже добавлен.")
            ingr_ids.add(cur_id)

        return data

    def get_ingredients(self, obj: Recipe):
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

    def get_is_favorited(self, obj: Recipe):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj: Recipe):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()


class RecipeCreateUpdateDeleteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    author = CustomUserProfileSerializer(read_only=True)

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

    def add_tags_ingredients(self, obj: Recipe, tags_data=None, ingredients_data=None):
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
        tags_data = validated_data.pop("tags")
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self.add_tags_ingredients(recipe, tags_data, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.image = validated_data.get("image", instance.image)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        instance.image = validated_data.get("image", instance.image)
        instance.text = validated_data.get("text", instance.text)
        self.add_tags_ingredients(obj=instance)
        instance.save()
        return instance


class FavoritesShoppingCartSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class ShortLinkSerializer(serializers.ModelSerializer):
    short_code = serializers.SerializerMethodField()

    class Meta:
        model = Link
        fields = ("short_code",)

    def get_short_code(self, obj: Link):
        if not obj.short_link:
            LINK_CHARS = ascii_lowercase + ascii_uppercase + digits
            chars_len = len(LINK_CHARS) - 1
            short_code = "".join(LINK_CHARS[randint(0, chars_len)] for i in range(7))
            # short_url = self.request.build_absolute_uri("/") + short_code
            short_url = short_code
            # Link.objects.get_or_create(original_link= ??, short_link=short_url)
            return
        return short_url
