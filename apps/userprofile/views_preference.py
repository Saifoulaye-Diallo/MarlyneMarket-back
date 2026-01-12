from rest_framework import viewsets, permissions
from .models_preference import UserPreference
from .serializers_preference import UserPreferenceSerializer
from .permissions_preference import IsOwnerOrAdmin

class UserPreferenceViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les préférences utilisateur.
    - Un utilisateur ne peut voir/modifier que ses propres préférences (sauf admin).
    - Un seul objet UserPreference par utilisateur.
    """
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserPreference.objects.all()
        return UserPreference.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
