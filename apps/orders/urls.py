"""
URL configuration for orders app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.orders.views import (
    CustomerOrderViewSet,
    SellerOrderViewSet,
    AdminOrderViewSet,
)

# Customer routes - uses DefaultRouter for proper list/retrieve
customer_router = DefaultRouter(trailing_slash=True)
customer_router.register(r'', CustomerOrderViewSet, basename='customer-order')

# Seller routes - uses DefaultRouter for proper list/retrieve
seller_router = DefaultRouter(trailing_slash=True)
seller_router.register(r'', SellerOrderViewSet, basename='seller-order')

# Admin routes - uses DefaultRouter for proper list/retrieve
admin_router = DefaultRouter(trailing_slash=True)
admin_router.register(r'', AdminOrderViewSet, basename='admin-order')

urlpatterns = [
    # Seller endpoints: /api/orders/seller/
    path('seller/', include(seller_router.urls)),
    
    # Admin endpoints: /api/orders/admin/
    path('admin/', include(admin_router.urls)),
    
    # Customer endpoints: /api/orders/ (must be last due to empty prefix)
    path('', include(customer_router.urls)),
]
