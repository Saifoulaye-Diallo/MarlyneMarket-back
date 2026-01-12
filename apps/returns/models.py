"""
Return request models with complete information.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid

from apps.orders.models import OrderItem


class ReturnRequest(models.Model):
    """
    Complete return/refund request model for order items.
    Tracks entire return lifecycle from request to refund.
    """
    
    STATUS_CHOICES = [
        ('requested', _('Requested')),
        ('initiated', _('Return Initiated')),
        ('pending_approval', _('Pending Approval')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('pending_return_shipping', _('Pending Return Shipping')),
        ('in_transit', _('In Transit')),
        ('received_by_seller', _('Received by Seller')),
        ('inspection_in_progress', _('Inspection In Progress')),
        ('inspected', _('Inspected')),
        ('refunded', _('Refunded')),
        ('cancelled', _('Cancelled')),
    ]
    
    REASON_CHOICES = [
        ('defective', _('Defective Product')),
        ('wrong_item', _('Wrong Item Received')),
        ('not_as_described', _('Not As Described')),
        ('damaged_in_shipping', _('Damaged in Shipping')),
        ('missing_parts', _('Missing Parts')),
        ('no_longer_needed', _('No Longer Needed')),
        ('changed_mind', _('Changed Mind')),
        ('other', _('Other')),
    ]
    
    REFUND_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processed', _('Processed')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='return_requests',
        verbose_name=_('Order Item'),
        db_index=True
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='return_requests',
        verbose_name=_('Customer'),
        db_index=True
    )
    
    seller = models.ForeignKey(
        'accounts.SellerProfile',
        on_delete=models.CASCADE,
        related_name='return_requests',
        verbose_name=_('Seller'),
        null=True,
        blank=True
    )
    
    # Return Information
    reason = models.CharField(
        max_length=50,
        choices=REASON_CHOICES,
        verbose_name=_('Return Reason')
    )
    
    description = models.TextField(
        verbose_name=_('Return Description')
    )
    
    # Return Status
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='initiated',
        db_index=True,
        verbose_name=_('Return Status')
    )
    
    # Return Shipping Information
    return_shipping_label = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Return Shipping Label')
    )
    
    return_tracking_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Return Tracking Number')
    )
    
    return_carrier = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Return Carrier')
    )
    
    # Refund Information
    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Refund Amount')
    )
    
    refund_status = models.CharField(
        max_length=20,
        choices=REFUND_STATUS_CHOICES,
        default='pending',
        verbose_name=_('Refund Status')
    )
    
    refund_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Refund Reason')
    )
    
    refund_initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initiated_returns',
        verbose_name=_('Refund Initiated By')
    )
    
    # Inspection Information
    inspection_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Inspection Notes')
    )
    
    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspected_returns',
        verbose_name=_('Inspected By')
    )
    
    # Seller/Admin Response
    response_note = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Response Note')
    )
    
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='return_responses',
        verbose_name=_('Responded By')
    )
    
    # Deduction Information (if applicable)
    deduction_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Deduction Amount')
    )
    
    deduction_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Deduction Reason')
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
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Responded At')
    )
    received_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Received At')
    )
    inspected_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Inspected At')
    )
    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Refunded At')
    )
    
    class Meta:
        verbose_name = _('Return Request')
        verbose_name_plural = _('Return Requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order_item']),
            models.Index(fields=['status']),
            models.Index(fields=['refund_status']),
        ]
    
    def __str__(self):
        return f"Return #{self.pk} - {self.order_item.title_snapshot} ({self.status})"
