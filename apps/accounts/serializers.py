from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SellerProfile, UserAddress

User = get_user_model()


class UserAddressSerializer(serializers.ModelSerializer):
    """Serializer for user addresses"""
    
    class Meta:
        model = UserAddress
        fields = [
            'id', 'user', 'address_type', 'is_default',
            'recipient_name', 'phone_number', 'street_address',
            'apartment_number', 'postal_code', 'city',
            'state_province', 'country', 'address_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with complete profile"""
    
    addresses = UserAddressSerializer(
        source='user_addresses',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'profile_picture_url', 'biography',
            'role', 'account_status', 'email_verified', 'email_verified_at',
            'two_factor_enabled', 'last_login_ip', 'is_active',
            'created_at', 'updated_at', 'deleted_at', 'addresses'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'last_login_ip',
            'email_verified_at', 'deleted_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """Update user, handling password separately"""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class SellerProfileSerializer(serializers.ModelSerializer):
    """Serializer for SellerProfile with all business information"""
    
    user_email = serializers.CharField(
        source='user.email',
        read_only=True
    )
    
    user_first_name = serializers.CharField(
        source='user.first_name',
        read_only=True
    )
    
    user_last_name = serializers.CharField(
        source='user.last_name',
        read_only=True
    )
    
    class Meta:
        model = SellerProfile
        fields = [
            'id', 'user', 'user_email', 'user_first_name', 'user_last_name',
            'shop_name', 'shop_slug', 'shop_description', 'shop_logo_url',
            'shop_banner_url', 'business_type', 'business_registration_number',
            'tax_identification_number', 'primary_phone', 'secondary_phone',
            'support_email', 'street_address', 'building_number', 'city',
            'state_province', 'postal_code', 'country', 'bank_account_holder_name',
            'bank_account_number', 'bank_routing_number', 'bank_code', 'bank_country',
            'approval_status', 'approved_by', 'approval_note', 'approved_at',
            'total_products', 'average_rating', 'total_reviews', 'total_orders',
            'response_time_hours', 'seller_level', 'auto_accept_returns',
            'return_days', 'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = [
            'id', 'approved_by', 'approved_at', 'total_products',
            'average_rating', 'total_reviews', 'total_orders',
            'created_at', 'updated_at', 'deleted_at'
        ]
        extra_kwargs = {
            'bank_account_number': {'write_only': True},
            'bank_routing_number': {'write_only': True},
            'tax_identification_number': {'write_only': True}
        }

    def get_full_address(self, obj):
        """Return formatted full address"""
        return obj.get_full_address()


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed User serializer"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class TokenObtainSerializer(serializers.Serializer):
    """Authenticate user and return token."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    raise serializers.ValidationError('Invalid credentials')
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid credentials')

            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')

        return attrs


class SellerProfileDetailSerializer(serializers.ModelSerializer):
    """Detail serializer for SellerProfile - uses existing fields"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = SellerProfile
        fields = [
            'id', 'user', 'user_email', 'user_full_name', 'shop_name',
            'shop_description', 'business_type', 'country',
            'approval_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_user_full_name(self, obj):
        return obj.user.get_full_name() if obj.user else ""
