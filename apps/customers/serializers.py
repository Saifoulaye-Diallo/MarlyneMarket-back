from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import CustomerProfile, Address

User = get_user_model()


class CustomerAddressSerializer(serializers.ModelSerializer):
    """Serializer for customer addresses"""
    
    class Meta:
        model = Address
        fields = [
            'id', 'user', 'label', 'full_name', 'phone_number',
            'email_address', 'street_address', 'apartment_number',
            'city', 'state_province', 'postal_code', 'country',
            'delivery_instructions', 'is_default_shipping',
            'is_default_billing', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerProfileSerializer(serializers.ModelSerializer):
    """Serializer for CustomerProfile with all preference and loyalty data"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    addresses = CustomerAddressSerializer(
        source='user.customer_addresses',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'user', 'user_email', 'user_first_name', 'user_last_name',
            'phone_number', 'date_of_birth', 'gender', 'preferred_language',
            'preferred_currency', 'subscribe_to_newsletter',
            'receive_promotional_emails', 'receive_order_notifications',
            'total_orders', 'total_spent', 'loyalty_points', 'customer_tier',
            'company_name', 'last_order_at', 'created_at', 'updated_at',
            'addresses'
        ]
        read_only_fields = [
            'id', 'total_orders', 'total_spent', 'loyalty_points',
            'last_order_at', 'created_at', 'updated_at'
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.role = "customer"
        user.set_password(password)
        user.save()
        CustomerProfile.objects.create(user=user)
        return user


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "label",
            "full_name",
            "phone_number",
            "email_address",
            "street_address",
            "building_apartment",
            "city",
            "state_province",
            "postal_code",
            "country",
            "delivery_instructions",
            "is_default_shipping",
            "is_default_billing",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        # ensure at least one of shipping/billing can be default per user
        user = self.context["request"].user if "request" in self.context else None
        if not user or not user.is_authenticated:
            return attrs
        if attrs.get("is_default_shipping"):
            Address.objects.filter(user=user, is_default_shipping=True).update(
                is_default_shipping=False
            )
        if attrs.get("is_default_billing"):
            Address.objects.filter(user=user, is_default_billing=True).update(
                is_default_billing=False
            )
        return attrs
