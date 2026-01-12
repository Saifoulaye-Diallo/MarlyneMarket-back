"""
Permissions for returns app.
"""
from rest_framework.permissions import BasePermission


class IsReturnOwner(BasePermission):
    """Allow customers to access only their own return requests."""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.user == request.user


class IsReturnSeller(BasePermission):
    """Allow sellers to access returns for their products."""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if not hasattr(request.user, 'seller_profile'):
            return False
        return obj.order_item.seller == request.user.seller_profile
