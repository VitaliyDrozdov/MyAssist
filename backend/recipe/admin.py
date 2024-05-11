from django.contrib import admin
from recipe.models import (
    Recipe,
    Favorite,
    ShoppingCart,
    Ingredient,
    Tag,
    RecipeIngredient,
)


admin.site.empty_value_display = "Null"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "author",
        "name",
        "image",
        "text",
        "is_favorited",
        "is_in_shopping_cart",
        "pub_date",
        "get_tag",
        "cnt_favoties",
    )
    list_editable = (
        "name",
        "image",
        "text",
        "is_favorited",
        "is_in_shopping_cart",
    )
    list_display_links = ("author",)
    search_fields = ("author", "name")
    list_filter = ("tags",)

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
    pass


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount")
    list_editable = ("amount",)
    list_display_links = ("recipe", "ingredient")
