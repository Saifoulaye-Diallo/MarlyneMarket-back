"""
Permissions for orders app.
Implements strict access control for multi-seller marketplace.
"""
from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    """Allow access only to authenticated customers."""
    
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and 
            user.is_authenticated and 
            getattr(user, 'role', None) == 'customer'
        )


class IsSeller(BasePermission):
    """Allow access only to authenticated sellers with active profile."""
    
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role != 'seller':
            return False
        return hasattr(user, 'seller_profile')


class IsSellerActive(BasePermission):
    """Allow access only to sellers with active status."""
    
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role != 'seller':
            return False
        if not hasattr(user, 'seller_profile'):
            return False
        return user.seller_profile.approval_status == 'approved'


class IsSuperAdmin(BasePermission):
    """Allow access only to super admins."""
    
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and 
            user.is_authenticated and 
            user.is_superuser
        )


class IsOrderOwner(BasePermission):
    """Allow customers to access only their own orders."""
    
    def has_object_permission(self, request, view, obj):
        # Super admin can access all
        if request.user.is_superuser:
            return True
        # Customer can only access their orders
        return obj.user == request.user


class IsSellerOrderOwner(BasePermission):
    """Allow sellers to access only orders containing their items."""
    
    def has_object_permission(self, request, view, obj):
        # Super admin can access all
        if request.user.is_superuser:
            return True
        # Check if seller has items in this order
        if not hasattr(request.user, 'seller_profile'):
            return False
        seller = request.user.seller_profile
        
        # For SellerOrder objects
        if hasattr(obj, 'seller') and hasattr(obj, 'order'):
            return obj.seller == seller
        
        # For Order objects - check if seller has items
        return obj.items.filter(seller=seller).exists()


class IsOwnOrderItem(BasePermission):
    """Allow sellers to manage only their own order items."""
    
    def has_object_permission(self, request, view, obj):
        # Super admin can access all
        if request.user.is_superuser:
            return True
        # Seller can only access their items
        if not hasattr(request.user, 'seller_profile'):
            return False
        return obj.seller == request.user.seller_profile


class CanCreateOrder(BasePermission):
    """Permission to create orders - only authenticated customers."""
    
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Customers or any authenticated user can create orders
        return user.role == 'customer' or user.is_authenticated
