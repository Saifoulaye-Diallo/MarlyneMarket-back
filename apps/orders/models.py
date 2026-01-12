"""
Orders models for marketplace.
Supports multi-seller orders where a single order can contain items from multiple sellers.
"""
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from apps.accounts.models import SellerProfile
from apps.catalog.models import Product


class Order(models.Model):
    """
    Main order model. Contains items from potentially multiple sellers.
    Shipping address is stored as JSON snapshot to preserve history.
    """
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', _('Unpaid')),
        ('paid', _('Paid')),
        ('refunded', _('Refunded')),
        ('failed', _('Failed')),
    ]
    
    CURRENCY_CHOICES = [
        ('EUR', 'Euro'),
        ('USD', 'US Dollar'),
        ('GBP', 'British Pound'),
        ('XOF', 'CFA Franc'),
    ]

    # Customer
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('Customer')
    )
    
    # Order reference
    reference = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name=_('Order Reference')
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name=_('Status')
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid',
        db_index=True,
        verbose_name=_('Payment Status')
    )
    
    # Financial
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Subtotal')
    )
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Tax')
    )
    shipping_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Shipping Fee')
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Discount')
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Total Amount')
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='EUR',
        verbose_name=_('Currency')
    )
    
    # Coupon (optional)
    coupon_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Coupon Code')
    )
    
    # Shipping address snapshot (JSON)
    shipping_address = models.JSONField(
        default=dict,
        verbose_name=_('Shipping Address')
    )
    
    # Billing address snapshot (JSON, optional)
    billing_address = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Billing Address')
    )
    
    # Notes
    customer_note = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Customer Note')
    )
    admin_note = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Admin Note')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'payment_status']),
            models.Index(fields=['reference']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.reference}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)
    
    def _generate_reference(self):
        """Generate unique order reference."""
        import uuid
        from django.utils import timezone
        date_str = timezone.now().strftime('%Y%m%d')
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"ORD-{date_str}-{unique_id}"
    
    def calculate_totals(self):
        """Recalculate order totals from items."""
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.total_amount = self.subtotal + self.tax + self.shipping_fee - self.discount
        return self.total_amount
    
    @property
    def seller_ids(self):
        """Return list of unique seller IDs in this order."""
        return list(self.items.values_list('seller_id', flat=True).distinct())


class OrderItem(models.Model):
    """
    Individual item in an order. Links to seller for multi-seller support.
    Product info is snapshot at order time.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Order')
    )
    seller = models.ForeignKey(
        SellerProfile,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('Seller')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('Product')
    )
    
    # Snapshot data (preserved even if product changes)
    title_snapshot = models.CharField(
        max_length=255,
        verbose_name=_('Product Title')
    )
    price_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Unit Price')
    )
    
    # Quantity and total
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Quantity')
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Line Total')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order', 'seller']),
            models.Index(fields=['seller']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.title_snapshot} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate line_total
        self.line_total = Decimal(str(self.price_snapshot)) * self.quantity
        super().save(*args, **kwargs)


class SellerOrder(models.Model):
    """
    Seller-specific view of an order.
    Allows sellers to manage their portion of multi-seller orders.
    """
    
    SELLER_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    ]
    
    seller = models.ForeignKey(
        SellerProfile,
        on_delete=models.CASCADE,
        related_name='seller_orders',
        verbose_name=_('Seller')
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='seller_orders',
        verbose_name=_('Order')
    )
    
    # Seller-specific status
    status = models.CharField(
        max_length=20,
        choices=SELLER_STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    
    # Shipping info
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Tracking Number')
    )
    carrier = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Carrier')
    )
    
    # Seller subtotal (sum of their items)
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Subtotal')
    )
    
    # Notes
    seller_note = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Seller Note')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Seller Order')
        verbose_name_plural = _('Seller Orders')
        ordering = ['-created_at']
        unique_together = ['seller', 'order']
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"{self.seller.shop_name} - {self.order.reference}"
    
    def calculate_subtotal(self):
        """Calculate subtotal from seller's items in this order."""
        self.subtotal = sum(
            item.line_total 
            for item in self.order.items.filter(seller=self.seller)
        )
        return self.subtotal
    
    @property
    def items(self):
        """Get all order items belonging to this seller."""
        return self.order.items.filter(seller=self.seller)


class EmailLog(models.Model):
    """
    Log des emails envoyés pour traçabilité.
    Enregistre tous les emails de confirmation de commande.
    """
    
    STATUS_CHOICES = [
        ('sent', _('Envoyé')),
        ('failed', _('Échec')),
        ('pending', _('En attente')),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='email_logs',
        verbose_name=_('Commande')
    )
    
    recipient = models.EmailField(
        verbose_name=_('Destinataire')
    )
    
    subject = models.CharField(
        max_length=255,
        verbose_name=_('Sujet')
    )
    
    body = models.TextField(
        verbose_name=_('Contenu')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Statut')
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Message d\'erreur')
    )
    
    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Envoyé le')
    )
    
    class Meta:
        verbose_name = _('Email Log')
        verbose_name_plural = _('Email Logs')
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['-sent_at']),
        ]
    
    def __str__(self):
        return f"Email à {self.recipient} - {self.order.reference} ({self.status})"
