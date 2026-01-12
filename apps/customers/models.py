from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
import uuid


class CustomerProfile(models.Model):
    """Complete customer profile with all necessary information."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
        verbose_name=_('User')
    )
    
    # Profile Information
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
    
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date of Birth')
    )
    
    gender = models.CharField(
        max_length=20,
        choices=[
            ('male', _('Male')),
            ('female', _('Female')),
            ('other', _('Other')),
            ('prefer_not_to_say', _('Prefer not to say')),
        ],
        blank=True,
        null=True,
        verbose_name=_('Gender')
    )
    
    # Preferences
    preferred_language = models.CharField(
        max_length=10,
        choices=[(code, name) for code, name in settings.LANGUAGES],
        default='en',
        verbose_name=_('Preferred Language')
    )
    
    preferred_currency = models.CharField(
        max_length=3,
        choices=[
            ('EUR', 'Euro'),
            ('USD', 'US Dollar'),
            ('GBP', 'British Pound'),
            ('XOF', 'CFA Franc'),
        ],
        default='EUR',
        verbose_name=_('Preferred Currency')
    )
    
    # Newsletter & Communication
    subscribe_to_newsletter = models.BooleanField(
        default=True,
        verbose_name=_('Subscribe to Newsletter')
    )
    
    receive_promotional_emails = models.BooleanField(
        default=True,
        verbose_name=_('Receive Promotional Emails')
    )
    
    receive_order_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Receive Order Notifications')
    )
    
    # Customer Metrics
    total_orders = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total Orders')
    )
    
    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Total Spent')
    )
    
    loyalty_points = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Loyalty Points')
    )
    
    customer_tier = models.CharField(
        max_length=20,
        choices=[
            ('bronze', _('Bronze')),
            ('silver', _('Silver')),
            ('gold', _('Gold')),
            ('platinum', _('Platinum')),
        ],
        default='bronze',
        verbose_name=_('Customer Tier')
    )
    
    # Account Information
    company_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Company Name')
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
    
    last_order_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last Order At')
    )

    class Meta:
        verbose_name = _("Customer Profile")
        verbose_name_plural = _("Customer Profiles")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['customer_tier']),
        ]

    def __str__(self) -> str:  # type: ignore[override]
        return f"{self.user.get_full_name()} ({self.user.email})"


class Address(models.Model):
    """Complete customer address with all necessary information."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_addresses",
        verbose_name=_('User')
    )
    
    # Address Label & Type
    label = models.CharField(
        max_length=100,
        default="Home",
        choices=[
            ('home', _('Home')),
            ('work', _('Work')),
            ('other', _('Other')),
        ],
        verbose_name=_('Address Label')
    )
    
    # Recipient Information
    full_name = models.CharField(
        max_length=255,
        verbose_name=_('Full Name')
    )
    
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
    
    email_address = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Email Address')
    )
    
    # Address Components
    street_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Street Address')
    )
    
    building_apartment = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Building/Apartment Number')
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Postal Code')
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
    
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Country')
    )
    
    # Additional Information
    delivery_instructions = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Delivery Instructions')
    )
    
    # Default Addresses
    is_default_shipping = models.BooleanField(
        default=False,
        verbose_name=_('Default Shipping Address')
    )
    
    is_default_billing = models.BooleanField(
        default=False,
        verbose_name=_('Default Billing Address')
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
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_default_shipping']),
            models.Index(fields=['is_default_billing']),
        ]

    def __str__(self) -> str:  # type: ignore[override]
        return f"{self.label} - {self.full_name} ({self.city}, {self.country})"
    
    def get_formatted_address(self):
        """Return formatted address string."""
        parts = [
            self.street_address,
            self.building_apartment,
            self.postal_code,
            self.city,
            self.state_province,
            self.country,
        ]
        return ', '.join(filter(None, parts))
