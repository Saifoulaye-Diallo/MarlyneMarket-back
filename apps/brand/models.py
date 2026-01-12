from django.db import models

class Brand(models.Model):
    """
    Marque de produit, pour filtres, pages marque, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='brands/logos/', blank=True, null=True)

    class Meta:
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
        ordering = ['name']

    def __str__(self):
        return self.name