from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.customers.models import CustomerProfile, Address
from apps.customers.serializers import (
    RegisterSerializer,
    CustomerProfileSerializer,
    AddressSerializer,
)
from apps.customers.permissions import IsAddressOwner


class RegisterView(generics.CreateAPIView):
    """Public registration endpoint for customers."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    """Get/Update the authenticated customer's profile."""

    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = CustomerProfile.objects.get_or_create(user=self.request.user)
        return profile


class AddressViewSet(viewsets.ModelViewSet):
    """Manage addresses of the authenticated customer."""

    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated, IsAddressOwner]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
