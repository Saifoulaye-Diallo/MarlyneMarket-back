from django.db import models
from django.conf import settings
from apps.catalog.models import Product

class CartItem(models.Model):
    """
    Un article de panier lié à un utilisateur connecté.
    Unicité user+product : un même produit ne peut apparaître qu'une fois par utilisateur.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='in_carts')
    quantity = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return f"{self.user} - {self.product} (x{self.quantity})"