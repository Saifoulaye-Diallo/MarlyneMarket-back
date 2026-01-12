from rest_framework import permissions

class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    - Lecture : tout le monde
    - Création : utilisateur authentifié
    - Modification/suppression : propriétaire ou admin
    - Validation (is_approved) : admin uniquement
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return obj.user == request.user
