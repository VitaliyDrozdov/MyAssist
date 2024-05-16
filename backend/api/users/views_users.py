from django.contrib.auth import get_user_model

from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewset
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST


from api.pagination import LimitPagination
from api.users.serializers_users import (
    CustomUserProfileSerializer,
    SubscribeSerializer,
    SubscribeGetSerializer,
    AvatarSerializer,
)
from users.models import Subscription

User = get_user_model()


class UserViewSet(DjoserUserViewset):
    queryset = User.objects.all()
    serializer_class = CustomUserProfileSerializer
    pagination_class = LimitPagination

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="subscribe",
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        following = get_object_or_404(User, id=self.kwargs.get("id"))
        user = request.user.id
        if request.method == "POST":
            serializer = SubscribeSerializer(
                data={"user": user, "following": self.kwargs.get("id")},
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            cur_sub = Subscription.objects.filter(following=following, user=user)
            if not cur_sub.exists():
                return Response(status=HTTP_400_BAD_REQUEST)
            cur_sub.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        url_path="subscriptions",
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = User.objects.filter(following__user=user)
        if subscriptions:
            pages = self.paginate_queryset(subscriptions)
            serializer = SubscribeGetSerializer(
                pages, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)
        else:
            return Response("Подписки отсутствуют", status=HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=["put", "patch", "delete"],
        url_path="me/avatar",
        permission_classes=(IsAuthenticated,),
    )
    def set_avatar(self, request):
        if request.method == "PUT" or request.method == "PATCH":
            serializer = AvatarSerializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "DELETE":
            request.user.avatar.delete(save=True)
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
