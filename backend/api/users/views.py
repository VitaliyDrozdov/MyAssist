from django.contrib.auth import get_user_model

from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewset
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from api.pagination import LimitPagination
from api.users.serializers import (
    CustomUserProfileSerializer,
    SubscribeSerializer,
    SubscribeGetSerializer,
    AvatarSerializer,
)
from users.models import Subscription

User = get_user_model()


class UserViewSet(DjoserUserViewset):
    """ViewSet для пользователей. Унаследован от Djoser.
    Регистрация, авторизация, подписки на других пользователей,
    список подписок, изменение аватара у пользователя.
    Настройки Djoser переопределены в settings.py
    """

    queryset = User.objects.all()
    serializer_class = CustomUserProfileSerializer
    pagination_class = LimitPagination

    @action(
        detail=True,
        methods=["post"],
        url_path="subscribe",
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs) -> Response:
        """Создаёт связь между пользователями.
        Args:
            request: Request.
        Returns:
            Response: статус подписки.
        """
        serializer = SubscribeSerializer(
            data={
                "user": get_object_or_404(User, id=request.user.id).id,
                "following": get_object_or_404(
                    User, id=self.kwargs.get("id")
                ).id,
            },
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs) -> Response:
        """Удалет связь между пользователями.
        Args:
            request: Request.
        Returns:
            Response: статус подписки.
        """
        following = get_object_or_404(User, id=self.kwargs.get("id"))
        user = request.user.id
        deleted, _ = Subscription.objects.filter(
            following=following, user=user
        ).delete()
        if not deleted:
            response_status = status.HTTP_400_BAD_REQUEST
            response_data = "Пользователь отсутствует в подписках."
        else:
            response_status = status.HTTP_204_NO_CONTENT
            response_data = None
        return Response(response_data, status=response_status)

    @action(
        detail=False,
        methods=["get"],
        url_path="subscriptions",
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request) -> Response:
        """Показывает всех юзеров на которых подписан текущий пользователь.
        Дополнительно показываются созданные рецепты.
        Args:
            request: Request.
        Returns:
            Response: список подписок.
        """
        subscriptions = User.objects.filter(following__user=request.user)
        pages = self.paginate_queryset(subscriptions)
        serializer = SubscribeGetSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False, methods=["get"],
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs) -> Response:
        """Переопределение методов для эндпоинта /me/."""
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=["put"],
        url_path="me/avatar",
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request) -> Response:
        """Изменение аватара."""
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request) -> Response:
        """Удаление аватара."""
        request.user.avatar.delete(save=True)
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
