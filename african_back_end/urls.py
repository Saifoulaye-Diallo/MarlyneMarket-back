from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.routers import SimpleRouter
from apps.catalog.views import PublicProductViewSet, SellerProductsOnlyViewSet
from apps.accounts.views import (
    AdminUserListView, AdminSellerListView, AdminProductListView,
    CustomerProfileDetailView, SellerProfileDetailView
)
from apps.promotions.views import ValidateCouponView, ValidateCouponAltView
from apps.orders.views import SellerOrderListView, SellerOrderItemListView, SellerOrderItemDetailView, SellerAnalyticsView

# Public routes
public_router = SimpleRouter()
public_router.register(r'products', PublicProductViewSet, basename='product')

# Seller routes (reuse the same ProductViewSet)
seller_router = SimpleRouter()
seller_router.register(r'products', SellerProductsOnlyViewSet, basename='seller-product')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Public API endpoints (at /api/products/)
    path('api/', include(public_router.urls)),
    
    # Seller API endpoints (at /api/seller/products/)
    path('api/seller/', include(seller_router.urls)),
    
    # Seller-specific endpoints
    path('api/seller/orders/', SellerOrderItemListView.as_view(), name='seller-orders'),
    path('api/seller/order-items/<int:id>/', SellerOrderItemDetailView.as_view(), name='seller-order-item-detail'),
    path('api/seller/analytics/', SellerAnalyticsView.as_view(), name='seller-analytics'),
    
    # Profile endpoints
    path('api/customer/profile/<uuid:id>/', CustomerProfileDetailView.as_view(), name='customer-profile-detail'),
    path('api/seller/profile/<int:id>/', SellerProfileDetailView.as_view(), name='seller-profile-detail'),
    path('api/sellers/<int:id>/', SellerProfileDetailView.as_view(), name='seller-detail'),
    
    # Search endpoint (delegated to products list with search param)
    path('api/products/search/', PublicProductViewSet.as_view({'get': 'list'}), name='product-search'),
    
    # Admin API endpoints
    path('api/admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('api/admin/sellers/', AdminSellerListView.as_view(), name='admin-sellers'),
    path('api/admin/products/', AdminProductListView.as_view(), name='admin-products'),
    
    # Coupons endpoint (alternative path with 404 for non-existent)
    path('api/coupons/validate/', ValidateCouponAltView.as_view(), name='validate-coupon-alt'),
    
    # API Endpoints
    path('api/auth/', include('apps.accounts.urls')),
    path('api/catalog/', include('apps.catalog.urls')),
    path('api/customers/', include('apps.customers.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/returns/', include('apps.returns.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
    path('api/promotions/', include('apps.promotions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
