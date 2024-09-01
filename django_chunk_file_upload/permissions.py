from __future__ import annotations


class BasePermission:
    safe_methods = ("GET", "POST", "DELETE")

    def has_permission(self, request, view) -> bool:
        return False

    def is_safe_method(self, request, view) -> bool:
        return bool(
            str(request.method).upper() in [m.upper() for m in self.safe_methods]
        )


class AllowAny(BasePermission):
    def has_permission(self, request, view) -> bool:
        if self.is_safe_method(request, view):
            return True
        return False


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view) -> bool:
        if self.is_safe_method(request, view):
            return bool(request.user and request.user.is_authenticated)
        return False


class IsSuperUser(BasePermission):
    def has_permission(self, request, view) -> bool:
        if self.is_safe_method(request, view):
            return bool(request.user and request.user.is_superuser)
        return False


class IsAdminUser(BasePermission):
    def has_permission(self, request, view) -> bool:
        if self.is_safe_method(request, view):
            return bool(
                request.user and (request.user.is_staff or request.user.is_superuser)
            )
        return False


class IsStaffUser(BasePermission):
    def has_permission(self, request, view) -> bool:
        if self.is_safe_method(request, view):
            return bool(request.user and request.user.is_staff)
        return False


class IsAuthenticatedOrReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        if self.is_safe_method(request, view):
            return bool(
                request.user
                and (request.user.is_authenticated or request.user.is_superuser)
            )
        return False
