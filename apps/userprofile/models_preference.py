from django.db import models
from django.conf import settings

class UserPreference(models.Model):
    """
    Préférences utilisateur (langue, notifications, etc.).
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preference')
    language = models.CharField(max_length=10, default='fr')
    notifications_enabled = models.BooleanField(default=True)
    # Ajoute d'autres préférences ici

    class Meta:
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'

    def __str__(self):
        return f"Préférences de {self.user}"