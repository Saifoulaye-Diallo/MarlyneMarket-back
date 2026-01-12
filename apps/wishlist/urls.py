from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WishlistItemViewSet

router = DefaultRouter()
router.register(r'wishlist', WishlistItemViewSet, basename='wishlist')

urlpatterns = [
    path('', include(router.urls)),
]
