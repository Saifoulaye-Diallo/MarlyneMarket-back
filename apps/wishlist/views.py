from rest_framework import viewsets, permissions
from .models import WishlistItem
from .serializers import WishlistItemSerializer
from .permissions import IsOwnerOrAdmin

class WishlistItemViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les favoris utilisateur (Wishlist).
    - Un utilisateur ne peut voir/modifier que ses propres favoris (sauf admin).
    - Unicité user+product garantie côté modèle.
    """
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return WishlistItem.objects.all()
        return WishlistItem.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
