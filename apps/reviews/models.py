"""
Review models with complete information.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
import uuid

from apps.catalog.models import Product


class Review(models.Model):
    """
    Complete product review model from verified purchases.
    Includes moderation, ratings, and helpfulness tracking.
    """
    
    RATING_CHOICES = [
        (1, _('1 - Poor')),
        (2, _('2 - Fair')),
        (3, _('3 - Good')),
        (4, _('4 - Very Good')),
        (5, _('5 - Excellent')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending Approval')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Reviewer'),
        db_index=True
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Product'),
        db_index=True
    )
    
    # Rating
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('Rating')
    )
    
    # Review Content
    title = models.CharField(
        max_length=255,
        verbose_name=_('Review Title')
    )
    
    comment = models.TextField(
        verbose_name=_('Review Comment')
    )
    
    # Verified Purchase
    is_verified_purchase = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('Verified Purchase')
    )
    
    order_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Order Reference')
    )
    
    # Moderation
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name=_('Status')
    )
    
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reviews',
        verbose_name=_('Moderated By')
    )
    
    moderation_note = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Moderation Note')
    )
    
    # Review Metrics
    helpful_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Helpful Count')
    )
    
    unhelpful_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Unhelpful Count')
    )
    
    # Seller Response
    seller_response = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Seller Response')
    )
    
    response_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Response At')
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
    
    moderated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Moderated At')
    )
    
    class Meta:
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')
        ordering = ['-created_at']
        unique_together = ['user', 'product']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['user']),
            models.Index(fields=['is_verified_purchase']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name} ({self.rating}★)"


class ReviewHelpful(models.Model):
    """
    Track helpful/unhelpful votes on reviews by other users.
    Helps identify useful reviews for other shoppers.
    """
    
    VOTE_CHOICES = [
        ('helpful', _('Helpful')),
        ('unhelpful', _('Unhelpful')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpful_votes',
        verbose_name=_('Review'),
        db_index=True
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_helpful_votes',
        verbose_name=_('Voter'),
        db_index=True
    )
    
    vote_type = models.CharField(
        max_length=20,
        choices=VOTE_CHOICES,
        default='helpful',
        verbose_name=_('Vote Type')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('Review Helpful Vote')
        verbose_name_plural = _('Review Helpful Votes')
        unique_together = ['review', 'user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['review', 'vote_type']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.email} marked review as {self.vote_type}"
