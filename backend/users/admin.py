from django.contrib import admin

from users.models import CustomUser, Subscription


@admin.register(CustomUser)
class CustomUserModel(admin.ModelAdmin):
    pass


@admin.register(Subscription)
class Subscription(admin.ModelAdmin):
    pass
