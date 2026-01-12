"""
URL configuration for promotions app.
"""
from django.urls import path, include
from rest_framework.routers import SimpleRouter

from apps.promotions.views import (
    ValidateCouponView,
    PublicCouponListView,
    SellerCouponViewSet,
    AdminCouponViewSet,
)

seller_router = SimpleRouter()
seller_router.register(r'', SellerCouponViewSet, basename='seller-coupon')

admin_router = SimpleRouter()
admin_router.register(r'', AdminCouponViewSet, basename='admin-coupon')

urlpatterns = [
    path('', PublicCouponListView.as_view(), name='public-coupons'),
    path('validate/', ValidateCouponView.as_view(), name='validate-coupon'),
    path('seller/', include(seller_router.urls)),
    path('admin/', include(admin_router.urls)),
]
