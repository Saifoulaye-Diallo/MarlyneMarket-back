"""
Serializers for promotions app.
"""
from rest_framework import serializers
from .models import Coupon, CouponUsage


class CouponUsageSerializer(serializers.ModelSerializer):
    """Serializer for coupon usage tracking"""
    
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon', 'coupon_code', 'user', 'user_email', 'order',
            'original_amount', 'discount_amount', 'final_amount',
            'is_refunded', 'refund_amount', 'refunded_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CouponSerializer(serializers.ModelSerializer):
    """Serializer for coupons with complete promotion management"""
    
    seller_name = serializers.CharField(source='seller.shop_name', read_only=True, allow_null=True)
    usage_count = serializers.SerializerMethodField()
    remaining_uses = serializers.SerializerMethodField()
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name', 'description', 'seller', 'seller_name', 'discount_type',
            'discount_value', 'status', 'is_stackable', 'applies_to_sale_items',
            'require_email_subscription', 'max_purchase_amount',
            'min_purchase_amount', 'usage_limit', 'usage_limit_per_user',
            'usage_count', 'remaining_uses', 'start_date', 'end_date',
            'categories', 'products', 'excluded_categories',
            'created_at', 'updated_at', 'is_valid', 'is_active', 'scope'
        ]
        read_only_fields = [
            'id', 'usage_count', 'remaining_uses', 'created_at', 'updated_at', 'is_valid'
        ]
    
    def get_usage_count(self, obj):
        return CouponUsage.objects.filter(coupon=obj).count()
    
    def get_remaining_uses(self, obj):
        if obj.usage_limit:
            usage_count = CouponUsage.objects.filter(coupon=obj).count()
            return max(0, obj.usage_limit - usage_count)
        return None


class ValidateCouponSerializer(serializers.Serializer):
    """Validate coupon serializer."""
    
    code = serializers.CharField(max_length=50)
    cart_total = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2,
        required=False
    )
    
    def validate(self, attrs):
        from django.utils import timezone
        from django.db import transaction
        from django.db.models import F
        
        user = self.context['request'].user
        code = attrs['code']
        cart_total = attrs.get('cart_total')
        
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({'code': 'Coupon does not exist'})
        
        # Check if coupon is active
        now = timezone.now()
        if coupon.start_date and coupon.start_date > now:
            raise serializers.ValidationError({'code': 'Coupon is not yet active'})
        
        if coupon.end_date and coupon.end_date < now:
            raise serializers.ValidationError({'code': 'Coupon has expired'})
        
        # Check total usage limit before attempting to use
        if coupon.usage_limit and coupon.times_used >= coupon.usage_limit:
            raise serializers.ValidationError({'code': 'Coupon usage limit reached'})
        
        # Check per-user usage limit
        user_usage_count = CouponUsage.objects.filter(coupon=coupon, user=user).count()
        if user_usage_count >= coupon.usage_limit_per_user:
            raise serializers.ValidationError({'code': 'You have already used this coupon'})
        
        # Check min purchase amount
        if cart_total and coupon.min_purchase_amount and cart_total < coupon.min_purchase_amount:
            raise serializers.ValidationError({
                'cart_total': f'Minimum purchase amount is {coupon.min_purchase_amount}'
            })
        
        # Atomic operation: increment usage count and check limit
        with transaction.atomic():
            # Update usage count atomically using F() expression
            updated = Coupon.objects.filter(
                id=coupon.id,
                usage_limit__isnull=False,
                times_used__lt=F('usage_limit')
            ).update(times_used=F('times_used') + 1)
            
            # If usage_limit is None, just increment
            if coupon.usage_limit is None:
                Coupon.objects.filter(id=coupon.id).update(times_used=F('times_used') + 1)
                updated = 1
            
            if not updated:
                raise serializers.ValidationError({'code': 'Coupon usage limit reached'})
            
            # Create coupon usage record
            CouponUsage.objects.create(
                coupon=coupon,
                user=user,
                order=None,
                discount_amount=0
            )
        
        # Refresh coupon to get updated values
        coupon.refresh_from_db()
        attrs['coupon'] = coupon
        return attrs


class CouponResponseSerializer(serializers.Serializer):
    """Coupon validation response."""
    
    code = serializers.CharField()
    discount_type = serializers.CharField()
    discount_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    estimated_discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    min_purchase_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class AdminCouponSerializer(serializers.ModelSerializer):
    """Admin coupon serializer with full details."""
    
    created_by_email = serializers.EmailField(
        source='created_by.email',
        read_only=True
    )
    seller_name = serializers.CharField(
        source='seller.shop_name',
        read_only=True
    )
    category_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            'id',
            'code',
            'description',
            'discount_type',
            'discount_value',
            'min_purchase_amount',
            'max_discount_amount',
            'usage_limit',
            'usage_limit_per_user',
            'times_used',
            'start_date',
            'end_date',
            'is_active',
            'scope',
            'categories',
            'category_names',
            'seller',
            'seller_name',
            'created_by',
            'created_by_email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'times_used', 'created_by', 'created_at', 'updated_at']
    
    def get_category_names(self, obj):
        return list(obj.categories.values_list('name', flat=True))
    
    def create(self, validated_data):
        categories = validated_data.pop('categories', [])
        validated_data['created_by'] = self.context['request'].user
        coupon = super().create(validated_data)
        if categories:
            coupon.categories.set(categories)
        return coupon
    
    def update(self, instance, validated_data):
        categories = validated_data.pop('categories', None)
        coupon = super().update(instance, validated_data)
        if categories is not None:
            coupon.categories.set(categories)
        return coupon


class SellerCouponSerializer(serializers.ModelSerializer):
    """Seller coupon serializer (restricted scope)."""
    
    class Meta:
        model = Coupon
        fields = [
            'id',
            'code',
            'description',
            'discount_type',
            'discount_value',
            'min_purchase_amount',
            'max_discount_amount',
            'usage_limit',
            'usage_limit_per_user',
            'times_used',
            'start_date',
            'end_date',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'times_used', 'created_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['seller'] = user.seller_profile
        validated_data['scope'] = 'seller'
        return super().create(validated_data)


class CouponUsageSerializer(serializers.ModelSerializer):
    """Coupon usage serializer."""
    
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    order_reference = serializers.CharField(
        source='order.reference',
        read_only=True
    )
    
    class Meta:
        model = CouponUsage
        fields = [
            'id',
            'coupon',
            'coupon_code',
            'user',
            'user_email',
            'order',
            'order_reference',
            'discount_amount',
            'used_at',
        ]
