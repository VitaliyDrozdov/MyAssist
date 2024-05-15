from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(
        max_length=254, validators=[EmailValidator()], unique=True
    )
    username = models.CharField(
        verbose_name="Пользователь",
        max_length=150,
        unique=True,
        validators=[
            AbstractUser.username_validator,
        ],
    )
    first_name = models.CharField(verbose_name="Имя", max_length=150)
    last_name = models.CharField(verbose_name="Фамилия", max_length=150)
    password = models.CharField(verbose_name="Пароль", max_length=128)
    avatar = models.ImageField(
        verbose_name="Аватар", upload_to="avatars", null=True, blank=True
    )
    is_subscribed = models.BooleanField(verbose_name="Подписка", null=True)

    class Meta:
        verbose_name = "CustomUser"
        verbose_name_plural = "CustomUsers"

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        to=CustomUser,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Пользователь",
    )
    following = models.ForeignKey(
        to=CustomUser,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Подписчик",
    )

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "following"], name="unique_user_following"
            ),
            models.CheckConstraint(
                check=models.Q(user=models.F("user")), name="prevent_self_follow"
            ),
        ]

    def __str__(self):
        return self.user
