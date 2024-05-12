from random import choice, randint
from string import ascii_lowercase, ascii_uppercase, digits
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Ingredient(models.Model):
    # class MeasureChoices(models.TextChoices):
    #     GRAMM = "г", _("Граммы")
    #     DROP = "капля", _("Капля")
    #     PIECE = "шт.", _("Штуки")
    #     BIGPIECE = "кусок", _("Кусок")
    #     ML = "мл", _("Миллилитры")
    #     TEASPOON = "ч.л.", _("Чайная ложка")

    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name="Единицы измерения",
    )

    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(verbose_name="Имя тэга", max_length=25)
    slug = models.SlugField(verbose_name="Слаг", unique=True, max_length=50)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes", db_index=True
    )
    name = models.CharField(verbose_name="Наименование рецепта", max_length=256)
    image = models.ImageField(
        verbose_name="Изображение", upload_to="recipes", null=True, blank=True
    )
    text = models.TextField(verbose_name="Описание")
    ingredients = models.ManyToManyField(
        verbose_name="Ингредиенты",
        to=Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
    )
    tags = models.ManyToManyField(verbose_name="Тэг", to=Tag, related_name="recipes")
    cooking_time = models.IntegerField(
        verbose_name="Время приготовления", validators=[MinValueValidator(1)]
    )
    is_favorited = models.BooleanField(
        verbose_name="В избранном", blank=True, null=True
    )
    is_in_shopping_cart = models.BooleanField(
        verbose_name="В списке покупок", blank=True, null=True
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
    amount = models.IntegerField()

    class Meta:
        verbose_name = "RecipeIngredient"
        verbose_name_plural = "RecipeIngredients"


class Favorite(models.Model):
    user = models.ForeignKey(
        to=User, on_delete=models.CASCADE, related_name="favorites"
    )
    recipe = models.ForeignKey(
        to=Recipe, on_delete=models.CASCADE, related_name="favorites"
    )

    class Meta:
        verbose_name = "Favorite"
        verbose_name_plural = "Favorites"

    def __str__(self):
        return "Избранное"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        to=User, on_delete=models.CASCADE, related_name="shopping_cart"
    )
    recipe = models.ForeignKey(
        to=Recipe, on_delete=models.CASCADE, related_name="shopping_cart"
    )

    class Meta:
        verbose_name = "ShoppingCart"
        verbose_name_plural = "ShoppingCart"

    def __str__(self):
        return "Список покупок"


class Link(models.Model):
    original_link = models.URLField()
    short_link = models.SlugField(max_length=10, unique=True)

    class Meta:
        verbose_name = "Link"
        verbose_name_plural = "Links"

    def __str__(self):
        return self.short_link

    # def get_short_code(self, length=7):
    #     LINK_CHARS = ascii_lowercase + ascii_uppercase + digits
    #     chars_len = len(LINK_CHARS) - 1
    #     return "".join(LINK_CHARS[randint(0, chars_len)] for i in range(length))

    # def save(self, *args, **kwargs):
    #     if not self.pk:
    #         self.short_code = self.generate_short_code()
    #     return super().save(*args, **kwargs)
