from django.db import models
from django.conf import settings
from apps.catalog.models import Product

class WishlistItem(models.Model):
    """
    Un favori utilisateur. Permet de retrouver ses favoris sur tous ses appareils.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'

    def __str__(self):
        return f"{self.user} - {self.product}"