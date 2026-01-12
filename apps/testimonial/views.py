from rest_framework import viewsets, permissions
from .models import Testimonial
from .serializers import TestimonialSerializer
from .permissions import IsOwnerOrAdminOrReadOnly

class TestimonialViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les témoignages clients.
    - Lecture publique
    - Création : utilisateur authentifié
    - Modification/suppression : propriétaire ou admin
    - Validation (is_approved) : admin uniquement
    """
    serializer_class = TestimonialSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Testimonial.objects.all()
        # Les non-admins ne voient que les témoignages approuvés ou les leurs
        return Testimonial.objects.filter(models.Q(is_approved=True) | models.Q(user=user))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
