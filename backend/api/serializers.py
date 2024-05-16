import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

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
from api.users.serializers_users import (
    CustomUserProfileSerializer,
    CustomUserCreateSerializer,
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data: str):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


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
                raise serializers.ValidationError(
                    f"Количество должно быть положительным числом."
                )
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
        user = data.get("user")
        if user.shopping_cart.filter(recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже добавлен в список.")
        return data


class ShortLinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Link
        fields = ("original_link", "short_link", "short_code")
        extra_kwargs = {"short_code": {"write_only": True}}

    def create(self, validated_data):
        request = self.context.get("request")
        pk = self.initial_data.get("pk")
        recipe_detail_url = reverse("recipes-detail", args=[pk]).replace("api/", "")
        original_link = f"http://{request.META['HTTP_HOST']}{recipe_detail_url}"
        link, _ = Link.objects.get_or_create(
            original_link=original_link, **validated_data
        )
        return link

    def to_representation(self, instance):
        return {"short-link": instance.short_link}
