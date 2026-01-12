from rest_framework import viewsets
from .models import Brand
from .serializers import BrandSerializer
from .permissions import IsAdminOrReadOnly

class BrandViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les marques de produits.
    - Lecture publique
    - Création/modification/suppression : admin uniquement
    """
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrReadOnly]
