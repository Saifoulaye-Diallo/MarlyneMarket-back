from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Permission for super admin users only (catalog management)."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsOwnProduct(permissions.BasePermission):
    """
    Ensure seller can only access their own products.
    Object-level permission for product operations.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if not hasattr(request.user, 'seller_profile'):
            return False

        if hasattr(obj, 'seller'):
            return obj.seller == request.user.seller_profile

        if hasattr(obj, 'product'):
            return obj.product.seller == request.user.seller_profile

        return False
