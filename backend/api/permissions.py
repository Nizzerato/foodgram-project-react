from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Creating permissions of administrator."""

    def has_permission(self, request, view):
        """Enable permission of users."""
        if request.user.is_authenticated and request.user.is_admin:
            return True
        else:
            return False