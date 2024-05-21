from django.contrib import admin

from recipe.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)

from foodgram.constants import MIN_AMOUNT

admin.site.empty_value_display = "Null"


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 2
    min_num = MIN_AMOUNT


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "author",
        "name",
        "image",
        "text",
        "pub_date",
        "get_tag",
        "cnt_favoties",
    )
    list_editable = (
        "name",
        "image",
        "text",
    )
    list_display_links = ("author",)
    search_fields = ("author", "name")
    list_filter = ("tags",)

    inlines = (RecipeIngredientInline,)

    @admin.display(description="Тэг")
    def get_tag(self, obj):
        return ", ".join(tag.name for tag in obj.tags.all())

    @admin.display(description="Количество в избранном")
    def cnt_favoties(self, obj):
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient")
    list_display_links = ("recipe", "ingredient")
