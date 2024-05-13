from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS
            or (request.user and request.user.is_authenticated)
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and (request.user.is_staff or request.user == obj.author)
        )

    # def has_permission(self, request, view):
    #     return request.method in SAFE_METHODS or request.user.is_authenticated

    # def has_object_permission(self, request, view, obj):
    #     return obj.author == request.user or request.user.is_staff
