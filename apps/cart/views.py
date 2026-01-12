from rest_framework import viewsets, permissions
from .models import CartItem
from .serializers import CartItemSerializer
from .permissions import IsOwnerOrAdmin

class CartItemViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour le panier utilisateur (Cart).
    - Un utilisateur ne peut voir/modifier que ses propres articles (sauf admin).
    - Unicité user+product garantie côté modèle.
    - Ajout d'un produit déjà présent : incrémente la quantité.
    """
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CartItem.objects.all()
        return CartItem.objects.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        product = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity', 1)
        # Si l'article existe déjà, on incrémente la quantité
        cart_item, created = CartItem.objects.get_or_create(user=user, product=product, defaults={'quantity': quantity})
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        serializer.instance = cart_item
