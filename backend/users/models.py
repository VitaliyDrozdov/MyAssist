from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.db import models

from foodgram.constants import PASSWORD_MAX_LENGTH, USER_MAX_LENGTH


class CustomUser(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]
    email = models.EmailField(validators=[EmailValidator()], unique=True)
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=USER_MAX_LENGTH
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=USER_MAX_LENGTH
    )
    password = models.CharField(
        verbose_name="Пароль",
        max_length=PASSWORD_MAX_LENGTH
    )
    avatar = models.ImageField(
        verbose_name="Аватар", upload_to="avatars", null=True, blank=True
    )

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
                check=models.Q(
                    user=models.F("user")),
                name="prevent_self_follow"
            ),
        ]

    def __str__(self):
        return self.user
