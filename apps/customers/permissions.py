from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    """Allow access only to authenticated users with role=customer."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "role", None) == "customer")


class IsAddressOwner(BasePermission):
    """Object-level permission to allow customers to manage only their addresses."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
