import uuid
from string import ascii_lowercase, ascii_uppercase, digits

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
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
    short_link = models.SlugField(max_length=6, unique=True, editable=False)
    EMAIL_RANGDOM_CHARS = ascii_lowercase + ascii_uppercase + digits

    class Meta:
        verbose_name = "Link"
        verbose_name_plural = "Links"

    def __str__(self):
        return self.short_link

    @classmethod
    def create_short_link(cls, original_link):
        short_id = str(uuid.uuid4())[:3]
        short_link = f"https://foodgram.example.org/s/{short_id}"
        return cls.objects.create(original_link=original_link, short_link=short_link)

    # def __new__(cls, *args):
    #     length = len(cls.EMAIL_RANGDOM_CHARS) - 1
    #     short_code = "".join(
    #         cls.EMAIL_RANGDOM_CHARS[randint(0, length)] for _ in range(4)
    #     )
    #     short_link = (
    #         # f"https://foodgram.example.org/s/{slugify(uuid.uuid4().hex)[:6]}"
    #         f"https://foodgram.example.org/s/{short_code}"
    #     )
    #     setattr(cls, "short_link", short_link)
    #     return super().__new__(cls, *args)
