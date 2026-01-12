from rest_framework import serializers
from .models import UserAddress

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'user', 'address_line1', 'address_line2', 'city', 'country', 'postal_code', 'is_default']
        read_only_fields = ['id', 'user']
