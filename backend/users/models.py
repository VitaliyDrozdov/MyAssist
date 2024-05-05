from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.contrib.auth import get_user_model

# User = get_user_model()


class CustomUser(AbstractUser):
    email = models.EmailField(
        name="email", max_length=254, validators=[EmailValidator()]
    )
    username = models.CharField(
        name="Пользователь",
        max_length=150,
        unique=True,
        validators=[
            AbstractUser.username_validator,
        ],
    )
    first_name = models.CharField(name="Имя", max_length=150)
    last_name = models.CharField(name="Фамилия", max_length=150)
    password = models.CharField(name="Пароль", max_length=128)
    avatar = models.ImageField(
        name="Изображение", upload_to="avatars", null=True, blank=True
    )
    is_subscribed = models.BooleanField(name="Подписка")

    class Meta:
        verbose_name = "CustomUser"
        verbose_name_plural = "CustomUsers"

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        to=CustomUser, on_delete=models.CASCADE, related_name="follower"
    )
    following = models.ForeignKey(
        to=CustomUser, on_delete=models.CASCADE, related_name="following"
    )

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "following"], name="unique_user_following"
            ),
            models.CheckConstraint(
                check=models.Q(user=models.F("following")), name="prevent_self_follow"
            ),
        ]

    def __str__(self):
        return self.user
