import base64
from collections import OrderedDict


from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import QuerySet

from rest_framework import serializers
from rest_framework.reverse import reverse


from recipe.models import (
    Favorite,
    Ingredient,
    Link,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from api.users.serializers import CustomUserProfileSerializer

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Преобразование изображения в текстовую строку."""

    def to_internal_value(self, data: str):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext: str = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели тэгов."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для связанной модели рецепта и ингредиента."""

    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецептов."""

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

    def get_ingredients(self, obj: Recipe) -> QuerySet[Ingredient]:
        """Получение ингредиентов.
        Args:
            obj (Recipe): исходный рецепт.
        Returns:
            QuerySet: список ингридиентов.
        """
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

    def get_is_favorited(self, obj: Recipe) -> bool:
        """Проверяет статус избранного.
        Args:
            recipe (Recipe): Исходный рецепт.
        Returns:
            bool: true or false.
        """
        # user = self.context.get("request").user
        # if user.is_anonymous:
        #     return False
        # return user.favorites.filter(recipe=obj).exists()
        user = self.context.get("request").user
        return (
            self.context.get("request")
            and user.favorites.filter(user=user, recipe=obj).exists()
            and user.is_user_authenticated
        )

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        """Проверяет статус находится ли в списке покупок.
        Args:
            recipe (Recipe): Исходный рецепт.
        Returns:
            bool: true or false.
        """
        # user = self.context.get("request").user
        # if user.is_anonymous:
        #     return False
        # return user.shopping_cart.filter(recipe=obj).exists()
        user = self.context.get("request").user
        return (
            self.context.get("request")
            and user.shopping_cart.filter(user=user, recipe=obj).exists()
            and user.is_user_authenticated
        )


class RecipeCreateUpdateDeleteSerializer(serializers.ModelSerializer):
    """Сериализатор страницы рецепта."""

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

    def to_representation(self, intance: Recipe):
        return RecipeSerializer(intance, context=self.context).data

    def validate_ingredients(self, data: list[Ingredient]):
        if not data:
            raise serializers.ValidationError("Нужно указать ингредиенты.")
        ingr_ids = set()
        for ingredient in data:
            if not Ingredient.objects.filter(id=ingredient.get("id")).exists():
                raise serializers.ValidationError("Ингредиент не существует.")
            if not type(amount := ingredient.get("amount", 0)) is int:
                raise serializers.ValidationError(
                    "Количество должно быть положительным числом."
                )
            if amount <= 0:
                raise serializers.ValidationError("Количество должно быть больше нуля.")
            if (cur_id := ingredient.get("id")) in ingr_ids:
                raise serializers.ValidationError("Ингредиент уже добавлен.")
            ingr_ids.add(cur_id)
        return data

    def validate_tags(self, data: list[int]):
        if not data:
            raise serializers.ValidationError("Нужно указать тэги.")
        tag_ids = set()
        for tag in data:
            if tag in tag_ids:
                raise serializers.ValidationError("Тэг уже добавлен.")
            tag_ids.add(tag)
        return data

    def add_tags_ingredients(
        self,
        obj: Recipe,
        tags_data: list[int] = None,
        ingredients_data: OrderedDict = None,
    ) -> Recipe:
        """Добавлять тэги или ингредиенты к рецепту.
        Args:
            obj (Recipe): исходный рецепт.
            tags_data (list[int], optional): список с id тэгов.
            Defaults to None.
            ingredients_data (OrderedDict, optional):
            Список из словарей с ингредиентами. Defaults to None.
        Returns:
            Recipe: объект рецепта.
        """
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

    def create(self, validated_data: OrderedDict):
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
        instance.text = validated_data.get("text", instance.text)
        self.add_tags_ingredients(obj=instance)
        instance.save()
        return instance


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов с укороченными данными."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""

    class Meta:
        model = Favorite
        fields = (
            "user",
            "recipe",
        )

    def to_representation(self, instance: Favorite):
        return RecipeShortSerializer(
            instance.recipe, context={"request": self.context.get("request")}
        ).data

    def validate(self, data: OrderedDict):
        recipe = data.get("recipe")
        user = data.get("user")
        if user.favorites.filter(recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже добавлен в избранное.")
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = (
            "user",
            "recipe",
        )

    def to_representation(self, instance: ShoppingCart):
        return RecipeShortSerializer(
            instance.recipe, context={"request": self.context.get("request")}
        ).data

    def validate(self, data: OrderedDict):
        recipe = data.get("recipe")
        user = data.get("user")
        if user.shopping_cart.filter(recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже добавлен в список.")
        return data


class ShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор короткой ссылки."""

    class Meta:
        model = Link
        fields = ("original_link", "short_link", "short_code")
        extra_kwargs = {"short_code": {"write_only": True}}

    def create(self, validated_data):
        request = self.context.get("request")
        pk = self.initial_data.get("pk")
        recipe_detail_url = reverse("recipes-detail", args=[pk]).replace("api/", "")
        original_link = f"http://{request.META['HTTP_HOST']}" f"{recipe_detail_url}"
        link, _ = Link.objects.get_or_create(
            original_link=original_link, **validated_data
        )
        return link

    def to_representation(self, instance):
        return {"short-link": instance.short_link}
