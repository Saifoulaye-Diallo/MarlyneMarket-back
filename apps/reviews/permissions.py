"""
Permissions for reviews app.
"""
from rest_framework.permissions import BasePermission


class IsReviewOwner(BasePermission):
    """Allow users to manage their own reviews."""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.user == request.user
