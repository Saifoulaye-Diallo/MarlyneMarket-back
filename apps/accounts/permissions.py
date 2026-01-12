from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Permission for super admin users only."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsSeller(permissions.BasePermission):
    """Permission for authenticated seller users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'seller'
            and hasattr(request.user, 'seller_profile')
        )


class IsSellerOnly(permissions.BasePermission):
    """Permission that only allows sellers (denies customers and anonymous users)."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'seller'
            and hasattr(request.user, 'seller_profile')
        )


class IsSellerOrSuperAdmin(permissions.BasePermission):
    """Permission for sellers or super admins."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or (
                request.user.role == 'seller' and hasattr(request.user, 'seller_profile')
            ))
        )


class IsOwnProduct(permissions.BasePermission):
    """
    Ensure seller can only access their own products.
    Used for product and product image permissions.
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


class IsOwnSellerProfile(permissions.BasePermission):
    """Ensure users can only access their own seller profile."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.user == request.user
