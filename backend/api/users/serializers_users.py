import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer as DjoserCreateUS
from djoser.serializers import UserSerializer as DjoserMeUS
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

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
    class Meta:
        model = Subscription
        fields = ("user", "following")
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=["user", "following"],
            )
        ]

    def to_representation(self, instance):
        return SubscribeGetSerializer(
            instance.following, context={"request": self.context.get("request")}
        ).data

    def validate_following(self, val):
        if self.context["request"].user == val:
            raise serializers.ValidationError("Нельзя подписаться на себя.")
        return val


class SubscribeGetSerializer(CustomUserProfileSerializer):

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

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

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        from api.serializers import RecipeShortSerializer

        request = self.context.get("request")
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get("recipes_limit")
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data
