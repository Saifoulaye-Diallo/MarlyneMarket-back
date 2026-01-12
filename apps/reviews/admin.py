"""
Admin configuration for reviews app with updated field names.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display
from apps.reviews.models import Review, ReviewHelpful


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ['id', 'product', 'user_email', 'rating_badge', 'status_badge', 'verified_badge', 'created_at']
    list_filter = ['status', 'is_verified_purchase', 'rating', 'created_at']
    search_fields = ['user__email', 'product__name', 'comment', 'title']
    readonly_fields = ['created_at', 'updated_at', 'moderated_at', 'response_at', 'id']
    
    fieldsets = (
        (_('Review Info'), {
            'fields': ('id', 'user', 'product', 'rating', 'title', 'comment')
        }),
        (_('Verification'), {
            'fields': ('is_verified_purchase', 'order_reference')
        }),
        (_('Moderation'), {
            'fields': ('status', 'moderated_by', 'moderation_note', 'moderated_at')
        }),
        (_('Seller Response'), {
            'fields': ('seller_response', 'response_at'),
            'classes': ('collapse',)
        }),
        (_('Metrics'), {
            'fields': ('helpful_count', 'unhelpful_count'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_reviews', 'reject_reviews']
    list_per_page = 20
    ordering = ('-created_at',)
    
    @admin.action(description=_('Approve selected reviews'))
    def approve_reviews(self, request, queryset):
        updated = queryset.update(status='approved', moderated_by=request.user)
        self.message_user(request, f'{updated} reviews approved.')
    
    @admin.action(description=_('Reject selected reviews'))
    def reject_reviews(self, request, queryset):
        updated = queryset.update(status='rejected', moderated_by=request.user)
        self.message_user(request, f'{updated} reviews rejected.')
    
    @display(description=_('Email'), ordering='user__email')
    def user_email(self, obj):
        return obj.user.email
    
    @display(description=_('Rating'))
    def rating_badge(self, obj):
        colors = {
            1: '#dc2626',
            2: '#f97316',
            3: '#eab308',
            4: '#84cc16',
            5: '#22c55e',
        }
        color = colors.get(obj.rating, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}★</span>',
            color,
            obj.rating
        )
    
    @display(description=_('Status'), ordering='status')
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'approved': '#10b981',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @display(description=_('Verified'), boolean=True)
    def verified_badge(self, obj):
        return obj.is_verified_purchase


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(ModelAdmin):
    list_display = ['id', 'review', 'user_email', 'vote_badge', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['review__product__name', 'user__email']
    readonly_fields = ['created_at', 'id']
    
    fieldsets = (
        (_('Vote'), {
            'fields': ('id', 'review', 'user', 'vote_type', 'created_at')
        }),
    )
    
    list_per_page = 20
    ordering = ('-created_at',)
    
    @display(description=_('Email'), ordering='user__email')
    def user_email(self, obj):
        return obj.user.email
    
    @display(description=_('Vote Type'))
    def vote_badge(self, obj):
        colors = {
            'helpful': '#10b981',
            'unhelpful': '#ef4444',
        }
        color = colors.get(obj.vote_type, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_vote_type_display()
        )
