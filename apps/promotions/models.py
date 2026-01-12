"""
Promotion and coupon models with complete information.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

from apps.catalog.models import Category


class Coupon(models.Model):
    """
    Complete coupon/promo code model for discounts.
    Supports percentage and fixed amount discounts with flexible scoping.
    """
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', _('Percentage Discount')),
        ('fixed', _('Fixed Amount Discount')),
        ('free_shipping', _('Free Shipping')),
        ('buy_one_get_one', _('Buy One Get One')),
    ]
    
    SCOPE_CHOICES = [
        ('global', _('Global - All Products')),
        ('category', _('Category Specific')),
        ('seller', _('Seller Specific')),
        ('product', _('Product Specific')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('expired', _('Expired')),
        ('archived', _('Archived')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )

    # Basic Information
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_('Coupon Code')
    )
    
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Coupon Name')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    # Discount Configuration
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        verbose_name=_('Discount Type')
    )
    
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Discount Value')
    )
    
    # Discount Limits
    min_purchase_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Minimum Purchase Amount')
    )
    
    max_purchase_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('Maximum Purchase Amount')
    )
    
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('Maximum Discount Amount')
    )
    
    # Usage Limits
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Total Usage Limit')
    )
    
    usage_limit_per_user = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Usage Limit Per User')
    )
    
    times_used = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Times Used')
    )
    
    times_used_by_user = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Times Used by Current User')
    )
    
    # Validity Period
    start_date = models.DateTimeField(
        verbose_name=_('Start Date')
    )
    
    end_date = models.DateTimeField(
        verbose_name=_('End Date')
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
        verbose_name=_('Status')
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is Active')
    )
    
    # Scope Configuration
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='global',
        verbose_name=_('Coupon Scope')
    )
    
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='coupons',
        verbose_name=_('Applicable Categories')
    )
    
    products = models.ManyToManyField(
        'catalog.Product',
        blank=True,
        related_name='coupons',
        verbose_name=_('Applicable Products')
    )
    
    seller = models.ForeignKey(
        'accounts.SellerProfile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='coupons',
        verbose_name=_('Seller')
    )
    
    excluded_categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='excluded_from_coupons',
        verbose_name=_('Excluded Categories')
    )
    
    # Advanced Settings
    applies_to_sale_items = models.BooleanField(
        default=True,
        verbose_name=_('Applies to Sale Items')
    )
    
    is_stackable = models.BooleanField(
        default=False,
        verbose_name=_('Stackable with Other Coupons')
    )
    
    require_email_subscription = models.BooleanField(
        default=False,
        verbose_name=_('Require Email Subscription')
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_coupons',
        verbose_name=_('Created By')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('Coupon')
        verbose_name_plural = _('Coupons')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_valid(self):
        """Check if coupon is currently valid."""
        now = timezone.now()
        # Coupon is valid if:
        # 1. It's active
        # 2. Current time is within valid period
        # 3. Usage limits not reached
        if not self.is_active:
            return False
        if self.status not in ['active', 'draft']:  # Allow draft and active
            return False
        if now < self.start_date or now > self.end_date:
            return False
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        return True
        if now < self.start_date or now > self.end_date:
            return False
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        return True
    
    @property
    def remaining_uses(self):
        """Get remaining uses for this coupon."""
        if not self.usage_limit:
            return None
        return max(0, self.usage_limit - self.times_used)
    
    def calculate_discount(self, amount):
        """Calculate discount based on type and value."""
        if self.discount_type == 'percentage':
            discount = amount * (self.discount_value / 100)
        else:
            discount = self.discount_value
        
        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)
        
        return discount


class CouponUsage(models.Model):
    """
    Track detailed coupon usage by users.
    Maintains complete history of all coupon applications.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usages',
        verbose_name=_('Coupon'),
        db_index=True
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coupon_usages',
        verbose_name=_('User'),
        db_index=True
    )
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coupon_usages',
        verbose_name=_('Order')
    )
    
    # Discount Details
    original_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Original Amount')
    )
    
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Discount Amount')
    )
    
    final_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Final Amount')
    )
    
    # Refund Information
    is_refunded = models.BooleanField(
        default=False,
        verbose_name=_('Is Refunded')
    )
    
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Refund Amount')
    )
    
    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Refunded At')
    )
    
    # Timestamps
    used_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Used At')
    )
    
    class Meta:
        verbose_name = _('Coupon Usage')
        verbose_name_plural = _('Coupon Usages')
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['coupon', 'user']),
            models.Index(fields=['user']),
            models.Index(fields=['used_at']),
        ]
    
    def __str__(self):
        return f"{self.coupon.code} used by {self.user.email}"
