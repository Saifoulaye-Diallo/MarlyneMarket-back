"""
API views with translation support for multilingual catalog content.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django.utils.translation import get_language_from_request
from .models import (
    Category, ProductType, Attribute, AttributeOption,
    Product, ProductType
)
from .serializers_i18n import (
    TranslatedCategorySerializer,
    TranslatedProductTypeSerializer,
    TranslatedProductTypeSchemaSerializer,
    TranslatedAttributeSerializer,
    TranslatedProductSerializer,
)
from .i18n import get_language_code


class TranslationMixin:
    """
    Mixin that adds language code to serializer context from Accept-Language header.
    """
    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Get language from request
        lang = get_language_code(self.request)
        context['language_code'] = lang
        return context


class CategoryViewSet(TranslationMixin, viewsets.ModelViewSet):
    """
    API endpoint for categories with multilingual support.
    Returns translated content based on Accept-Language header.
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = TranslatedCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TranslatedCategorySerializer
        # Use standard serializer for write operations
        from .serializers import CategorySerializer
        return CategorySerializer


class ProductTypeViewSet(TranslationMixin, viewsets.ModelViewSet):
    """
    API endpoint for product types with multilingual support.
    Returns translated content based on Accept-Language header.
    """
    queryset = ProductType.objects.filter(is_active=True)
    serializer_class = TranslatedProductTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def schema(self, request, pk=None):
        """
        Get the dynamic form schema for a product type.
        Returns translated attribute names and options.
        """
        product_type = self.get_object()
        serializer = TranslatedProductTypeSchemaSerializer(
            product_type,
            context=self.get_serializer_context()
        )
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TranslatedProductTypeSerializer
        # Use standard serializer for write operations
        from .serializers import ProductTypeSerializer
        return ProductTypeSerializer


class AttributeViewSet(TranslationMixin, viewsets.ModelViewSet):
    """
    API endpoint for attributes with multilingual support.
    """
    queryset = Attribute.objects.filter(is_active=True)
    serializer_class = TranslatedAttributeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TranslatedAttributeSerializer
        # Use standard serializer for write operations
        from .serializers import AttributeSerializer
        return AttributeSerializer


class ProductViewSet(TranslationMixin, viewsets.ModelViewSet):
    """
    API endpoint for products with multilingual support.
    Returns translated content based on Accept-Language header.
    """
    serializer_class = TranslatedProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['category', 'product_type', 'status']

    def get_queryset(self):
        return Product.objects.filter(status='published').select_related('seller', 'category', 'product_type')

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TranslatedProductSerializer
        # Use standard serializer for write operations
        from .serializers import ProductSerializer
        return ProductSerializer


# ============================================================================
# Backward compatible endpoints (without translation)
# ============================================================================

class CategoryListViewSet(viewsets.ModelViewSet):
    """Legacy endpoint - use CategoryViewSet instead."""
    queryset = Category.objects.filter(is_active=True)
    from .serializers import CategorySerializer
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'


class ProductTypeListViewSet(viewsets.ModelViewSet):
    """Legacy endpoint - use ProductTypeViewSet instead."""
    queryset = ProductType.objects.filter(is_active=True)
    from .serializers import ProductTypeSerializer
    serializer_class = ProductTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProductListViewSet(viewsets.ModelViewSet):
    """Legacy endpoint - use ProductViewSet instead."""
    from .serializers import ProductSerializer
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Product.objects.filter(status='published').select_related('seller', 'category', 'product_type')
