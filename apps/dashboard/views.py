from rest_framework import viewsets, permissions
from .models import DashboardStat
from .serializers import DashboardStatSerializer
from .permissions import IsOwnerOrAdmin

class DashboardStatViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les statistiques dashboard persistantes.
    - Un utilisateur ne peut voir/modifier que ses propres stats (sauf admin).
    """
    serializer_class = DashboardStatSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return DashboardStat.objects.all()
        return DashboardStat.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
