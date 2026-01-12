from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserAddressViewSet

router = DefaultRouter()
router.register(r'addresses', UserAddressViewSet, basename='useraddress')

urlpatterns = [
    path('', include(router.urls)),
]
