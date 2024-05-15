import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer as DjoserCreateUS
from djoser.serializers import UserSerializer as DjoserMeUS
from rest_framework import serializers

from recipe.models import (
    Favorite,
    Ingredient,
    Link,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data: str):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)

    def validate(self, data):
        avatar = data.get("avatar", None)
        if not avatar:
            raise serializers.ValidationError("Необходимо прикрепить аватар.")
        return data


class CustomUserCreateSerializer(DjoserCreateUS):
    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name", "password")


class CustomUserProfileSerializer(DjoserMeUS):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

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
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_is_subscribed(self, obj: User):
        user = self.context.get("request").user
        if user.is_anonymous or obj == user:
            return False
        return Subscription.objects.filter(user=user, following=obj).exists()

    def validate(self, data):
        following_id = (
            self.context.get("request").parser_context.get("kwargs").get("id")
        )
        following = get_object_or_404(User, id=following_id)
        user = self.context.get("request").user
        if user.follower.filter(following=following_id).exists():
            raise serializers.ValidationError(detail="Подписка уже существует")
        if user == following:
            raise serializers.ValidationError(
                detail="Нельзя подписаться на самого себя"
            )
        return data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


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

    def to_representation(self, intance):
        return RecipeSerializer(intance, context=self.context).data

    def validate_ingredients(self, data):
        if not data:
            raise serializers.ValidationError("Нужно указать ингредиенты.")
        ingr_ids = set()
        for ingredient in data:
            if not Ingredient.objects.filter(id=ingredient.get("id")).exists():
                raise serializers.ValidationError(f"Ингредиент не существует.")
            if not type(amount := ingredient.get("amount", 0)) is int:
                raise serializers.ValidationError(f"Количество должно быть числом.")
            if amount <= 0:
                raise serializers.ValidationError(
                    f"Количество должно быть больше нуля."
                )
            if (cur_id := ingredient.get("id")) in ingr_ids:
                raise serializers.ValidationError(f"Ингредиент уже добавлен.")
            ingr_ids.add(cur_id)
        return data

    def validate_tags(self, data):
        if not data:
            raise serializers.ValidationError("Нужно указать тэги.")
        tag_ids = set()
        for tag in data:
            if tag in tag_ids:
                raise serializers.ValidationError(f"Тэг уже добавлен.")
            tag_ids.add(tag)
        return data

    def add_tags_ingredients(self, obj: Recipe, tags_data=None, ingredients_data=None):
        if "tags" in self.validated_data:
            tags_data = self.validated_data.pop("tags")
            obj.tags.set(tags_data)
        else:
            raise serializers.ValidationError("Нужно указать тэги.")
        if "ingredients" in self.validated_data:
            ingredients_data = self.validated_data.pop("ingredients")
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=obj,
                    ingredient=Ingredient.objects.get(id=ingredient_data["id"]),
                    amount=ingredient_data["amount"],
                )
        else:
            raise serializers.ValidationError("Нужно указать ингредиенты.")
        return obj

    def create(self, validated_data):
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


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор полей избранных рецептов и покупок"""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FavoritesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = (
            "user",
            "recipe",
        )

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe, context={"request": self.context.get("request")}
        ).data

    def validate(self, data):
        recipe = data.get("recipe")
        user = data.get("user")
        if user.favorites.filter(recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже добавлен в избранное.")
        return data

    # def favorite(self):
    #     user = self.context["request"].user
    #     recipe = self.context["recipe"]
    #     if user.favorites.filter(recipe=recipe).exists():
    #         raise serializers.ValidationError("Рецепт уже добавлен в избранное.")
    #     self.save()

    # def unfavorite(self):
    #     user = self.context["request"].user
    #     recipe = self.context["recipe"]
    #     favorite = user.favorites.filter(recipe=recipe).first()
    #     if favorite:
    #         favorite.delete()
    #     else:
    #         raise serializers.ValidationError(
    #             "Рецепт не найден в избранном пользователя."
    #         )


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = (
            "user",
            "recipe",
        )

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe, context={"request": self.context.get("request")}
        ).data

    def validate(self, data):
        recipe = data.get("recipe")
        # if not Recipe.objects.filter(id=recipe).exists():
        #     raise serializers.ValidationError("Рецепт Не существует.")
        user = data.get("user")
        if user.shopping_cart.filter(recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже добавлен в список.")
        return data


class ShortLinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Link
        fields = ("short_link",)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return {"short-link": representation["short_link"]}
