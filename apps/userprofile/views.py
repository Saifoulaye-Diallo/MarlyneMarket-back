from rest_framework import viewsets, permissions
from .models import UserAddress
from .serializers import UserAddressSerializer
from .permissions import IsOwnerOrAdmin

class UserAddressViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les adresses utilisateur enrichies.
    - Un utilisateur ne peut voir/modifier que ses propres adresses (sauf admin).
    - Un seul is_default=True par utilisateur (à gérer côté front ou via signal).
    """
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserAddress.objects.all()
        return UserAddress.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
