from django.db import models
from django.conf import settings

class UserAddress(models.Model):
    """
    Adresse utilisateur enrichie (multi-adresses, préférée, etc.).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'User Address'
        verbose_name_plural = 'User Addresses'
        ordering = ['user', '-is_default']

    def __str__(self):
        return f"{self.user} - {self.address_line1}, {self.city}"