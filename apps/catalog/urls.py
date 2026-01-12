from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_nested import routers

from apps.catalog.views import (
    AdminCategoryViewSet, AdminProductTypeViewSet, AdminAttributeViewSet,
    AdminAttributeOptionViewSet, AdminTypeAttributeRuleViewSet,
    ProductTypeSchemaView, SellerProductViewSet, SellerProductImageViewSet,
    SellerProductAttributeValueViewSet, PublicProductViewSet
)

# Public routes - no authentication
public_router = SimpleRouter()
public_router.register(r'products', PublicProductViewSet, basename='product')

# Admin routes - use SimpleRouter to avoid format suffix patterns conflict
router = SimpleRouter()
router.register(r'categories', AdminCategoryViewSet, basename='admin-category')
router.register(r'product-types', AdminProductTypeViewSet, basename='admin-product-type')
router.register(r'attributes', AdminAttributeViewSet, basename='admin-attribute')
router.register(r'attribute-options', AdminAttributeOptionViewSet, basename='admin-attribute-option')
router.register(r'type-attribute-rules', AdminTypeAttributeRuleViewSet, basename='admin-type-attribute-rule')

# Seller routes
seller_router = SimpleRouter()
seller_router.register(r'products', SellerProductViewSet, basename='seller-product')

# Nested routers for product images and attributes
products_router = routers.NestedSimpleRouter(seller_router, r'products', lookup='product')
products_router.register(r'images', SellerProductImageViewSet, basename='product-image')
products_router.register(r'attributes', SellerProductAttributeValueViewSet, basename='product-attribute-value')

urlpatterns = [
    # Public endpoints: /api/catalog/products/
    path('', include(public_router.urls)),
    
    # Admin endpoints
    path('admin/', include(router.urls)),
    path('admin/product-types/<int:pk>/schema/', ProductTypeSchemaView.as_view({'get': 'retrieve'}), name='product-type-schema'),
    
    # Seller endpoints
    path('seller/', include(seller_router.urls)),
    path('seller/', include(products_router.urls)),
]
