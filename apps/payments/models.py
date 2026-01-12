"""
Payment models for Stripe integration.
"""
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from apps.orders.models import Order


class Payment(models.Model):
    """
    Payment record for an order.
    Integrates with Stripe PaymentIntent.
    """
    
    STATUS_CHOICES = [
        ('created', _('Created')),
        ('pending', _('Pending')),
        ('succeeded', _('Succeeded')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    ]
    
    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('manual', 'Manual'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name=_('Order')
    )
    
    # Provider info
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='stripe',
        verbose_name=_('Payment Provider')
    )
    provider_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_('Provider Intent ID')
    )
    provider_charge_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Provider Charge ID')
    )
    
    # Amount
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Amount')
    )
    currency = models.CharField(
        max_length=3,
        default='EUR',
        verbose_name=_('Currency')
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        db_index=True,
        verbose_name=_('Status')
    )
    
    # Client secret for frontend
    client_secret = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Client Secret')
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata')
    )
    
    # Error handling
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Error Message')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['provider_intent_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.pk} - {self.order.reference} ({self.status})"


class Refund(models.Model):
    """
    Refund record for a payment.
    """
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('succeeded', _('Succeeded')),
        ('failed', _('Failed')),
    ]

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name=_('Payment')
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Amount')
    )
    
    reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Reason')
    )
    
    provider_refund_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Provider Refund ID')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    
    # Admin who initiated the refund
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='initiated_refunds',
        verbose_name=_('Initiated By')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Refund')
        verbose_name_plural = _('Refunds')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund {self.pk} - {self.amount} {self.payment.currency}"
