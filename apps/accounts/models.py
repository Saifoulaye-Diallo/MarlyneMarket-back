from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import uuid


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser with complete profile information.
    Supports multiple roles: super_admin, seller, customer, courier.
    """
    ROLE_CHOICES = [
        ('super_admin', _('Super Admin')),
        ('seller', _('Seller')),
        ('customer', _('Customer')),
        ('courier', _('Courier')),
    ]
    
    ACCOUNT_STATUS_CHOICES = [
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('suspended', _('Suspended')),
        ('banned', _('Banned')),
    ]

    # UUID primary key for better security
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    # Role management
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer',
        db_index=True,
        verbose_name=_('User Role')
    )
    
    # Profile information
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_('Invalid phone number format')
            )
        ],
        verbose_name=_('Phone Number')
    )
    
    profile_picture_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Profile Picture URL')
    )
    
    biography = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Biography')
    )
    
    # Account status
    account_status = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default='active',
        db_index=True,
        verbose_name=_('Account Status')
    )
    
    # Email verification
    email_verified = models.BooleanField(
        default=False,
        verbose_name=_('Email Verified')
    )
    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Email Verified At')
    )
    
    # Two-factor authentication
    two_factor_enabled = models.BooleanField(
        default=False,
        verbose_name=_('Two-Factor Authentication Enabled')
    )
    
    # Metadata
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('Last Login IP')
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
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Deleted At')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role', 'account_status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        full_name = self.get_full_name() or self.username
        return f"{full_name} ({self.email})" if self.email else full_name

    def is_seller(self):
        """Check if user is an active seller."""
        return self.role == 'seller' and self.account_status == 'active'

    def is_customer(self):
        """Check if user is an active customer."""
        return self.role == 'customer' and self.account_status == 'active'

    def is_super_admin(self):
        """Check if user is a super admin."""
        return (self.role == 'super_admin' or self.is_staff) and self.account_status == 'active'

    def is_courier(self):
        """Check if user is an active courier."""
        return self.role == 'courier' and self.account_status == 'active'


class UserAddress(models.Model):
    """
    User addresses for shipping and billing.
    """
    ADDRESS_TYPE_CHOICES = [
        ('shipping', _('Shipping Address')),
        ('billing', _('Billing Address')),
        ('both', _('Shipping & Billing')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_addresses',
        verbose_name=_('User')
    )
    
    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPE_CHOICES,
        default='shipping',
        verbose_name=_('Address Type')
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Default Address')
    )
    
    recipient_name = models.CharField(
        max_length=255,
        verbose_name=_('Recipient Name')
    )
    
    phone_number = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_('Invalid phone number format')
            )
        ],
        verbose_name=_('Phone Number')
    )
    
    street_address = models.CharField(
        max_length=255,
        verbose_name=_('Street Address')
    )
    
    apartment_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Apartment/Suite Number')
    )
    
    postal_code = models.CharField(
        max_length=20,
        verbose_name=_('Postal Code')
    )
    
    city = models.CharField(
        max_length=100,
        verbose_name=_('City')
    )
    
    state_province = models.CharField(
        max_length=100,
        verbose_name=_('State/Province')
    )
    
    country = models.CharField(
        max_length=100,
        verbose_name=_('Country')
    )
    
    address_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Address Notes')
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
        verbose_name = _('User Address')
        verbose_name_plural = _('User Addresses')
        ordering = ['-is_default', '-created_at']
        unique_together = ['user', 'recipient_name']

    def __str__(self):
        return f"{self.recipient_name} - {self.city}, {self.country}"
    
    def get_full_address(self):
        """Get formatted full address."""
        parts = [
            self.street_address,
            self.apartment_number,
            self.postal_code,
            self.city,
            self.state_province,
            self.country,
        ]
        return ', '.join(filter(None, parts))




class SellerProfile(models.Model):
    """
    Complete Seller profile model with all necessary information.
    Each seller is a user with extended business information and metrics.
    """
    APPROVAL_STATUS_CHOICES = [
        ('pending', _('Pending Approval')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('suspended', _('Suspended')),
        ('banned', _('Banned')),
    ]
    
    BUSINESS_TYPE_CHOICES = [
        ('individual', _('Individual')),
        ('business', _('Registered Business')),
        ('corporate', _('Corporate')),
    ]

    # Relationship to user
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='seller_profile',
        limit_choices_to={'role': 'seller'},
        verbose_name=_('User')
    )
    
    # Shop Information
    shop_name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name=_('Shop Name')
    )
    shop_slug = models.SlugField(
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Shop URL Slug')
    )
    shop_description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Shop Description')
    )
    shop_logo_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Shop Logo URL')
    )
    shop_banner_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Shop Banner URL')
    )
    
    # Business Information
    business_type = models.CharField(
        max_length=20,
        choices=BUSINESS_TYPE_CHOICES,
        default='individual',
        verbose_name=_('Business Type')
    )
    
    business_registration_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Business Registration Number')
    )
    
    tax_identification_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Tax ID Number')
    )
    
    # Contact Information
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_('Invalid phone number format')
            )
        ],
        verbose_name=_('Phone')
    )
    
    primary_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_('Invalid phone number format')
            )
        ],
        verbose_name=_('Primary Phone')
    )
    
    secondary_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Secondary Phone')
    )
    
    support_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Support Email')
    )
    
    # Business Address
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Address')
    )
    
    street_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Street Address')
    )
    
    building_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Building/Suite Number')
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('City')
    )
    
    state_province = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('State/Province')
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Postal Code')
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Country')
    )
    
    # Bank/Payment Information
    bank_account_holder_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Bank Account Holder Name')
    )
    
    bank_account_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Bank Account Number')
    )
    
    bank_routing_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Bank Routing Number')
    )
    
    bank_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Bank Code (SWIFT/BIC)')
    )
    
    bank_country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Bank Country')
    )
    
    # Approval Status
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name=_('Approval Status')
    )
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_sellers',
        verbose_name=_('Approved By')
    )
    
    approval_note = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Approval Note')
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Approved At')
    )
    
    # Seller Metrics
    total_products = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total Products')
    )
    
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name=_('Average Rating')
    )
    
    total_reviews = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total Reviews')
    )
    
    total_orders = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total Orders')
    )
    
    response_time_hours = models.PositiveIntegerField(
        default=24,
        verbose_name=_('Response Time (hours)')
    )
    
    seller_level = models.CharField(
        max_length=20,
        choices=[
            ('bronze', _('Bronze')),
            ('silver', _('Silver')),
            ('gold', _('Gold')),
            ('platinum', _('Platinum')),
        ],
        default='bronze',
        verbose_name=_('Seller Level')
    )
    
    # Settings & Preferences
    auto_accept_returns = models.BooleanField(
        default=False,
        verbose_name=_('Auto Accept Returns')
    )
    
    return_days = models.PositiveIntegerField(
        default=30,
        verbose_name=_('Return Days Allowed')
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
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Deleted At')
    )

    class Meta:
        verbose_name = _('Seller Profile')
        verbose_name_plural = _('Seller Profiles')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['approval_status']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
            models.Index(fields=['seller_level']),
        ]

    def __str__(self):
        return f"{self.shop_name} ({self.user.email})"
    
    @property
    def status(self):
        """Property to alias approval_status for backward compatibility."""
        return self.approval_status
    
    @status.setter
    def status(self, value):
        """Setter to allow setting status which maps to approval_status."""
        self.approval_status = value
    
    def get_full_address(self):
        """Get formatted full address."""
        parts = [
            self.street_address,
            self.building_number,
            self.postal_code,
            self.city,
            self.state_province,
            self.country,
        ]
        return ', '.join(filter(None, parts))


class BlacklistedAccessToken(models.Model):
    """Model to track blacklisted access tokens"""
    jti = models.CharField(max_length=255, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'blacklisted_access_tokens'
        indexes = [
            models.Index(fields=['jti']),
            models.Index(fields=['user']),
            models.Index(fields=['blacklisted_at']),
        ]
        
    def __str__(self):
        return f"Blacklisted token {self.jti[:8]}..."
