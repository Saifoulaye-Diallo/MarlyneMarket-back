from django.urls import path, include
from rest_framework.routers import SimpleRouter

from apps.customers.views import RegisterView, ProfileView, AddressViewSet

router = SimpleRouter()
router.register(r"addresses", AddressViewSet, basename="customer-address")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="customer-register"),
    path("profile/", ProfileView.as_view(), name="customer-profile"),
    path("", include(router.urls)),
]
