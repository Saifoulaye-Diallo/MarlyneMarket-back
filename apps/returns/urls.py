"""
URL configuration for returns app.
"""
from django.urls import path, include
from rest_framework.routers import SimpleRouter

from apps.returns.views import (
    CustomerReturnViewSet,
    SellerReturnViewSet,
    AdminReturnViewSet,
)

customer_router = SimpleRouter()
customer_router.register(r'', CustomerReturnViewSet, basename='customer-return')

seller_router = SimpleRouter()
seller_router.register(r'', SellerReturnViewSet, basename='seller-return')

admin_router = SimpleRouter()
admin_router.register(r'', AdminReturnViewSet, basename='admin-return')

urlpatterns = [
    path('', include(customer_router.urls)),
    path('seller/', include(seller_router.urls)),
    path('admin/', include(admin_router.urls)),
]
