from django.contrib import admin

from users.models import CustomUser, Subscription

admin.site.empty_value_display = "Null"


@admin.register(CustomUser)
class CustomUserModel(admin.ModelAdmin):
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "password",
        "avatar",
    )
    list_editable = (
        "username",
        "first_name",
        "last_name",
        "password",
        "avatar",
    )
    search_fields = ("username", "email")


@admin.register(Subscription)
class Subscription(admin.ModelAdmin):
    list_display = ("user", "following")
    list_editable = ("following",)
    list_display_links = ("user",)
