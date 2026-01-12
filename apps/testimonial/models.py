from django.db import models
from django.conf import settings
from apps.catalog.models import Product

class Testimonial(models.Model):
    """
    Témoignage client (avis produit ou général).
    Peut être modéré (is_approved).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='testimonials')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='testimonials')
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    date_created = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'
        ordering = ['-date_created']

    def __str__(self):
        return f"{self.user} - {self.product or 'Général'} ({self.rating}/5)"