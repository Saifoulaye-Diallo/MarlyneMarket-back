"""
Coupon validation service.
"""
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

from apps.promotions.models import Coupon, CouponUsage


class CouponService:
    """Service class for coupon validation and calculation."""
    
    @staticmethod
    def validate_coupon(code, user, cart_items=None, cart_total=None):
        """
        Validate a coupon code for a user.
        
        Args:
            code: Coupon code string
            user: User instance
            cart_items: List of cart items (optional, for scope validation)
            cart_total: Total cart amount (optional, for min purchase check)
        
        Returns:
            tuple: (is_valid, coupon_or_error_message)
        """
        with transaction.atomic():
            try:
                coupon = Coupon.objects.select_for_update().get(code__iexact=code)
            except Coupon.DoesNotExist:
                return False, "Invalid coupon code."
            
            # Check active status
            if not coupon.is_active:
                return False, "This coupon is no longer active."
            
            # Check date validity
            now = timezone.now()
            if now < coupon.start_date:
                return False, "This coupon is not yet valid."
            if now > coupon.end_date:
                return False, "This coupon has expired."
            
            # Check total usage limit
            if coupon.usage_limit and coupon.times_used >= coupon.usage_limit:
                return False, "This coupon has reached its usage limit."
            
            # Check per-user usage limit  
            user_usage = CouponUsage.objects.filter(coupon=coupon, user=user).count()
            if user_usage >= coupon.usage_limit_per_user:
                return False, "You have already used this coupon."
            
            # Check minimum purchase amount
            if cart_total is not None and cart_total < coupon.min_purchase_amount:
                return False, f"Minimum purchase amount of {coupon.min_purchase_amount} required."
            
            return True, coupon
    
    @staticmethod
    def calculate_discount(coupon, subtotal, applicable_amount=None):
        """
        Calculate discount amount for a coupon.
        
        Args:
            coupon: Coupon instance
            subtotal: Order subtotal
            applicable_amount: Amount the coupon applies to (for scoped coupons)
        
        Returns:
            Decimal: Discount amount
        """
        if applicable_amount is None:
            applicable_amount = subtotal
        
        if coupon.discount_type == 'percentage':
            discount = (applicable_amount * coupon.discount_value) / Decimal('100')
        else:  # fixed
            discount = min(coupon.discount_value, applicable_amount)
        
        # Apply max discount cap
        if coupon.max_discount_amount:
            discount = min(discount, coupon.max_discount_amount)
        
        return discount.quantize(Decimal('0.01'))
    
    @staticmethod
    def apply_coupon(coupon, user, order, discount_amount):
        """
        Record coupon usage.
        
        Args:
            coupon: Coupon instance
            user: User instance
            order: Order instance
            discount_amount: Calculated discount amount
        
        Returns:
            CouponUsage instance
        """
        with transaction.atomic():
            # Re-select coupon for update to ensure consistency
            coupon = Coupon.objects.select_for_update().get(pk=coupon.pk)
            
            # Double-check limits before applying
            if coupon.usage_limit and coupon.times_used >= coupon.usage_limit:
                raise ValueError("Coupon usage limit reached")
                
            user_usage = CouponUsage.objects.filter(coupon=coupon, user=user).count()
            if user_usage >= coupon.usage_limit_per_user:
                raise ValueError("User has already used this coupon")
            
            usage = CouponUsage.objects.create(
                coupon=coupon,
                user=user,
                order=order,
                discount_amount=discount_amount
            )
            
            # Increment usage count
            coupon.times_used += 1
            coupon.save(update_fields=['times_used'])
            
            return usage
    
    @staticmethod
    def get_applicable_amount(coupon, cart_items):
        """
        Calculate the amount a coupon applies to based on scope.
        
        Args:
            coupon: Coupon instance
            cart_items: List of dicts with 'product', 'quantity', 'price'
        
        Returns:
            Decimal: Amount the coupon applies to
        """
        if coupon.scope == 'global':
            return sum(
                item['price'] * item['quantity'] 
                for item in cart_items
            )
        
        applicable = Decimal('0')
        
        if coupon.scope == 'category':
            coupon_category_ids = set(coupon.categories.values_list('id', flat=True))
            for item in cart_items:
                product = item['product']
                if product.category_id in coupon_category_ids:
                    applicable += item['price'] * item['quantity']
        
        elif coupon.scope == 'seller':
            for item in cart_items:
                product = item['product']
                if product.seller_id == coupon.seller_id:
                    applicable += item['price'] * item['quantity']
        
        return applicable
