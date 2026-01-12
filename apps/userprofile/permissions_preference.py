from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission personnalisée : seul le propriétaire ou un admin peut accéder/modifier.
    """
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user
