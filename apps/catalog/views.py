from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes

from apps.catalog.models import (
    Category, ProductType, Attribute, AttributeOption,
    TypeAttributeRule, Product, ProductImage, ProductAttributeValue
)
from apps.catalog.serializers import (
    CategorySerializer, ProductTypeSerializer, AttributeSerializer,
    AttributeOptionSerializer, TypeAttributeRuleSerializer,
    ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, ProductImageSerializer,
    ProductAttributeValueSerializer, ProductTypeSchemaSerializer
)
from apps.catalog.permissions import IsSuperAdmin, IsOwnProduct
from apps.accounts.permissions import IsSeller, IsSellerOnly


class AdminCategoryViewSet(viewsets.ModelViewSet):
    """Admin viewset for managing product categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class AdminProductTypeViewSet(viewsets.ModelViewSet):
    """Admin viewset for managing product types."""
    queryset = ProductType.objects.prefetch_related('attribute_rules')
    serializer_class = ProductTypeSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class AdminAttributeViewSet(viewsets.ModelViewSet):
    """Admin viewset for managing attributes."""
    queryset = Attribute.objects.prefetch_related('options')
    serializer_class = AttributeSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'data_type']


class AdminAttributeOptionViewSet(viewsets.ModelViewSet):
    """Admin viewset for managing attribute options."""
    queryset = AttributeOption.objects.select_related('attribute')
    serializer_class = AttributeOptionSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [SearchFilter]
    search_fields = ['value', 'attribute__name']


class AdminTypeAttributeRuleViewSet(viewsets.ModelViewSet):
    """Admin viewset for managing type attribute rules."""
    queryset = TypeAttributeRule.objects.select_related('product_type', 'attribute')
    serializer_class = TypeAttributeRuleSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [OrderingFilter]
    ordering_fields = ['display_order', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        product_type_id = self.request.query_params.get('product_type')
        if product_type_id:
            queryset = queryset.filter(product_type_id=product_type_id)
        return queryset


class ProductTypeSchemaView(viewsets.ViewSet):
    """Read-only endpoint for getting product type schema (dynamic form)."""
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        """Get schema for a specific product type."""
        try:
            product_type = ProductType.objects.prefetch_related(
                'attribute_rules__attribute__options'
            ).get(pk=pk)
            serializer = ProductTypeSchemaSerializer(product_type)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ProductType.DoesNotExist:
            return Response(
                {'detail': 'Product type not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def list(self, request):
        """List all product types with their schemas."""
        product_types = ProductType.objects.filter(is_active=True).prefetch_related(
            'attribute_rules__attribute__options'
        )
        serializer = ProductTypeSchemaSerializer(product_types, many=True)
        return Response(serializer.data)


class SellerProductViewSet(viewsets.ModelViewSet):
    """Seller viewset for managing their own products."""
    permission_classes = [IsAuthenticated, IsSeller]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at', 'status']

    def get_queryset(self):
        """Sellers can only see their own products."""
        if not hasattr(self.request.user, 'seller_profile'):
            return Product.objects.none()
        return Product.objects.filter(
            seller=self.request.user.seller_profile
        ).select_related('seller', 'category', 'product_type').prefetch_related(
            'images', 'attribute_values__attribute'
        )

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        elif self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    def perform_create(self, serializer):
        """Automatically set seller to current user's profile."""
        serializer.save(seller=self.request.user.seller_profile)

    def perform_update(self, serializer):
        """Ensure seller cannot be changed."""
        serializer.save(seller=self.request.user.seller_profile)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a product (change status to published)."""
        product = self.get_object()
        self.check_object_permissions(request, product)

        if not product.can_be_published():
            return Response(
                {'detail': 'Product cannot be published. Required attributes are missing.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product.status = 'published'
        product.save()
        serializer = ProductDetailSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def draft(self, request, pk=None):
        """Move product to draft status."""
        product = self.get_object()
        self.check_object_permissions(request, product)
        product.status = 'draft'
        product.save()
        return Response({'status': 'draft'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """Disable a product."""
        product = self.get_object()
        self.check_object_permissions(request, product)
        product.status = 'disabled'
        product.save()
        return Response({'status': 'disabled'}, status=status.HTTP_200_OK)


class SellerProductImageViewSet(viewsets.ModelViewSet):
    """
    Seller viewset for managing product images with Cloudinary integration.
    
    Endpoints:
    - GET /api/seller/products/{product_id}/images/ - List product images
    - POST /api/seller/products/{product_id}/images/ - Upload new image
    - GET /api/seller/products/{product_id}/images/{id}/ - Get specific image
    - PATCH /api/seller/products/{product_id}/images/{id}/ - Update image metadata
    - DELETE /api/seller/products/{product_id}/images/{id}/ - Delete image
    """
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated, IsSeller, IsOwnProduct]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [OrderingFilter]
    ordering_fields = ['is_primary', 'created_at']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        """Sellers can only see images of their own products."""
        if not hasattr(self.request.user, 'seller_profile'):
            return ProductImage.objects.none()
        
        product_id = self.kwargs.get('product_pk')
        return ProductImage.objects.filter(
            product_id=product_id,
            product__seller=self.request.user.seller_profile
        ).select_related('product')

    def get_product(self):
        """Get the product from URL parameter and verify ownership."""
        product_id = self.kwargs.get('product_pk')
        try:
            return Product.objects.get(
                id=product_id,
                seller=self.request.user.seller_profile
            )
        except Product.DoesNotExist:
            return None

    @extend_schema(
        operation_id='seller_product_image_upload',
        summary='Upload product image',
        description='Upload an image for a product. Images are automatically stored on Cloudinary.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'image': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Image file (JPG, PNG, WEBP, max 5MB)'
                    },
                    'is_primary': {
                        'type': 'boolean',
                        'description': 'Set as primary image for product'
                    }
                },
                'required': ['image']
            }
        },
        responses={
            201: ProductImageSerializer,
            400: 'Validation error',
            403: 'Permission denied',
            404: 'Product not found'
        }
    )
    def create(self, request, *args, **kwargs):
        """Upload a new product image."""
        product = self.get_product()
        if not product:
            return Response(
                {'error': 'Product not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # The image will be automatically uploaded to Cloudinary via the ImageField
            image_instance = serializer.save(product=product)
            
            return Response(
                self.get_serializer(image_instance).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        """This method is called by create() above."""
        # Product is already set in create() method
        pass

    @extend_schema(
        operation_id='seller_product_image_set_primary',
        summary='Set image as primary',
        description='Set this image as the primary image for the product',
        request=None,
        responses={
            200: ProductImageSerializer,
            404: 'Image not found'
        }
    )
    @action(detail=True, methods=['post'], url_path='set-primary')
    def set_primary(self, request, product_pk=None, pk=None):
        """Set an image as primary for the product."""
        image = self.get_object()
        
        # Remove primary flag from all other images of this product
        ProductImage.objects.filter(
            product=image.product,
            is_primary=True
        ).update(is_primary=False)
        
        # Set this image as primary
        image.is_primary = True
        image.save()
        
        return Response(
            self.get_serializer(image).data,
            status=status.HTTP_200_OK
        )


class PublicProductViewSet(viewsets.ModelViewSet):
    """
    Unified ProductViewSet supporting multiple access levels:
    - Public: Can list and retrieve published products
    - Authenticated Seller: Can manage their own products
    - Admin: Can manage all products
    """
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at', 'average_rating']
    
    def get_permissions(self):
        """Allow different permissions based on action."""
        if self.action in ['list', 'retrieve']:
            # GET requests are always allowed (public read)
            return [AllowAny()]
        else:
            # POST/PUT/PATCH/DELETE requires seller or admin role
            from apps.accounts.permissions import IsSellerOrSuperAdmin
            return [IsAuthenticated(), IsSellerOrSuperAdmin()]
    
    def get_queryset(self):
        """Return appropriate products based on user role and action."""
        user = self.request.user
        
        # If user is not authenticated, show only published products
        if not user.is_authenticated:
            return Product.objects.filter(
                status='published',
                seller__approval_status='approved'
            ).select_related('seller', 'category', 'product_type').prefetch_related(
                'images', 'attribute_values__attribute'
            )
        
        # If user is admin, show all products
        if user.is_staff:
            return Product.objects.all().select_related(
                'seller', 'category', 'product_type'
            ).prefetch_related('images', 'attribute_values__attribute')
        
        # If user is a seller
        if hasattr(user, 'seller_profile'):
            # For list action, show ONLY their own products (product management endpoint)
            if self.action == 'list':
                return Product.objects.filter(
                    seller=user.seller_profile
                ).select_related('seller', 'category', 'product_type').prefetch_related(
                    'images', 'attribute_values__attribute'
                )
            else:
                # For other actions (retrieve, update, delete), show all products
                # Permission checks will be done in perform_* methods
                return Product.objects.all().select_related(
                    'seller', 'category', 'product_type'
                ).prefetch_related('images', 'attribute_values__attribute')
        
        # Regular customer - only published products
        return Product.objects.filter(
            status='published',
            seller__approval_status='approved'
        ).select_related('seller', 'category', 'product_type').prefetch_related(
            'images', 'attribute_values__attribute'
        )
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        elif self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    def perform_create(self, serializer):
        """Only sellers can create products."""
        if not hasattr(self.request.user, 'seller_profile'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only sellers can create products")
        serializer.save(seller=self.request.user.seller_profile)
    
    def perform_update(self, serializer):
        """Only owners or admins can update."""
        product = self.get_object()
        # If not admin and not owner, prevent update
        if not self.request.user.is_staff:
            if not hasattr(self.request.user, 'seller_profile') or product.seller != self.request.user.seller_profile:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only update your own products")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only owners or admins can delete."""
        if not self.request.user.is_staff:
            if not hasattr(self.request.user, 'seller_profile') or instance.seller != self.request.user.seller_profile:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only delete your own products")
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a product (change status to published)."""
        product = self.get_object()
        # Check permission
        if not request.user.is_staff and product.seller != request.user.seller_profile:
            return Response(
                {'detail': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not product.can_be_published():
            return Response(
                {'detail': 'Product cannot be published. Required attributes are missing.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product.status = 'published'
        product.save()
        serializer = ProductDetailSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def draft(self, request, pk=None):
        """Move product to draft status."""
        product = self.get_object()
        # Check permission
        if not request.user.is_staff and product.seller != request.user.seller_profile:
            return Response(
                {'detail': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        product.status = 'draft'
        product.save()
        return Response({'status': 'draft'}, status=status.HTTP_200_OK)


class SellerProductsOnlyViewSet(PublicProductViewSet):
    """
    ViewSet for /api/seller/products/ - Seller-only access to their own products.
    """
    permission_classes = [IsAuthenticated, IsSellerOnly]
    
    def list(self, request, *args, **kwargs):
        """Override list to check permissions explicitly."""
        if not (request.user and request.user.is_authenticated and 
                request.user.role == 'seller' and 
                hasattr(request.user, 'seller_profile')):
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        """Sellers can only see their own products."""
        if not hasattr(self.request.user, 'seller_profile'):
            return Product.objects.none()
        return Product.objects.filter(
            seller=self.request.user.seller_profile
        ).select_related('seller', 'category', 'product_type').prefetch_related(
            'images', 'attribute_values__attribute'
        )


class SellerProductAttributeValueViewSet(viewsets.ModelViewSet):
    """Seller viewset for managing product attribute values."""
    serializer_class = ProductAttributeValueSerializer
    permission_classes = [IsAuthenticated, IsSeller, IsOwnProduct]

    def get_queryset(self):
        """Sellers can only manage attributes of their own products."""
        if not hasattr(self.request.user, 'seller_profile'):
            return ProductAttributeValue.objects.none()
        return ProductAttributeValue.objects.filter(
            product__seller=self.request.user.seller_profile
        ).select_related('product', 'attribute', 'value_option')

    def get_product(self):
        """Get the product from URL parameter."""
        product_id = self.kwargs.get('product_pk')
        try:
            return Product.objects.get(
                id=product_id,
                seller=self.request.user.seller_profile
            )
        except Product.DoesNotExist:
            return None

    def perform_create(self, serializer):
        """Automatically set product from URL parameter."""
        product = self.get_product()
        if not product:
            raise serializers.ValidationError('Invalid product')
        serializer.save(product=product)
