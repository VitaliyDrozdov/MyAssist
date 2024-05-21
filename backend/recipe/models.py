from random import randint
from string import ascii_lowercase, ascii_uppercase, digits

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from foodgram import constants


User = get_user_model()


class Ingredient(models.Model):

    name = models.CharField(
        max_length=constants.CHAR_128_LENGTH, verbose_name="Наименование"
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name="Единицы измерения",
    )

    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_name_measurement_unit",
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        verbose_name="Имя тэга", max_length=constants.CHAR_32_LENGTH
    )
    slug = models.SlugField(
        verbose_name="Слаг", unique=True, max_length=constants.CHAR_32_LENGTH
    )

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes", db_index=True
    )
    name = models.CharField(
        verbose_name="Наименование рецепта", 
        max_length=constants.CHAR_256_LENGTH
    )
    image = models.ImageField(
        verbose_name="Изображение",
        upload_to="recipes",
        null=True,
        blank=True,
    )
    text = models.TextField(verbose_name="Описание")
    ingredients = models.ManyToManyField(
        verbose_name="Ингредиенты",
        to=Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
    )
    tags = models.ManyToManyField(
        verbose_name="Тэг",
        to=Tag, related_name="recipes"
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления",
        validators=[
            MinValueValidator(
                constants.MIN_TIME,
                f"Время не может быть меньше {constants.MIN_TIME}",
            ),
            MaxValueValidator(
                constants.MAX_TIME,
                f"Время не может быть больше {constants.MAX_TIME}",
            ),
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации", auto_now_add=True, db_index=True
    )

    class Meta:
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                constants.MIN_TIME,
                f"Количество не может быть меньше {constants.MIN_AMOUNT}",
            ),
            MaxValueValidator(
                constants.MAX_TIME,
                f"Количество не может быть больше {constants.MAX_AMOUNT}",
            ),
        ],
    )

    class Meta:
        verbose_name = "RecipeIngredient"
        verbose_name_plural = "RecipeIngredients"


class FavoriteShoppingBasemodel(models.Model):
    from recipe.models import Recipe

    user = models.ForeignKey(
        to=User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        to=Recipe, on_delete=models.CASCADE, verbose_name="Рецепт"
    )

    class Meta:
        abstract = True


class Favorite(FavoriteShoppingBasemodel):

    class Meta:
        verbose_name = "Favorite"
        verbose_name_plural = "Favorites"
        default_related_name = "favorites"

    def __str__(self):
        return "Избранное"


class ShoppingCart(FavoriteShoppingBasemodel):

    class Meta:
        verbose_name = "ShoppingCart"
        verbose_name_plural = "ShoppingCart"
        default_related_name = "shopping_cart"

    def __str__(self):
        return "Список покупок"


class Link(models.Model):
    original_link = models.URLField(blank=True)
    short_code = models.SlugField(max_length=5, unique=True, blank=True)
    EMAIL_RANGDOM_CHARS = ascii_lowercase + ascii_uppercase + digits
    __host = None

    class Meta:
        verbose_name = "Link"
        verbose_name_plural = "Links"

    def __str__(self):
        return self.short_link

    @classmethod
    def create_short_code(cls):
        length = len(cls.EMAIL_RANGDOM_CHARS) - 1
        short_code = "".join(
            cls.EMAIL_RANGDOM_CHARS[randint(0, length)] for _ in range(4)
        )
        return short_code

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.create_short_code()
        super().save(*args, **kwargs)

    @property
    def short_link(self):
        from foodgram import settings
        if not self.__host:
            self.__host = "localhost"
        port = getattr(settings, "PORT", None)
        if port:
            return f"http://{self.__host}:{port}/s/{self.short_code}"
        else:
            return f"http://{self.__host}/s/{self.short_code}"

    @short_link.setter
    def short_link(self, host):
        self.__host = str(host)
