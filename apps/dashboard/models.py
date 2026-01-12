from django.db import models
from django.conf import settings

class DashboardStat(models.Model):
    """
    Statistique persistante pour dashboard/analytics (ex : CA, nb commandes, etc.).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_stats')
    stat_type = models.CharField(max_length=100)
    value = models.FloatField()
    period = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dashboard Stat'
        verbose_name_plural = 'Dashboard Stats'
        ordering = ['-period', '-created_at']

    def __str__(self):
        return f"{self.user} - {self.stat_type} ({self.period}) : {self.value}"