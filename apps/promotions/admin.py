"""
Admin configuration for promotions app.
"""
from django.contrib import admin
from apps.promotions.models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'discount_type', 'discount_value', 
        'scope', 'is_active', 'times_used', 
        'start_date', 'end_date'
    ]
    list_filter = ['is_active', 'scope', 'discount_type', 'created_at']
    search_fields = ['code', 'description']
    filter_horizontal = ['categories']
    readonly_fields = ['times_used', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Discount', {
            'fields': (
                'discount_type', 'discount_value',
                'min_purchase_amount', 'max_discount_amount'
            )
        }),
        ('Usage Limits', {
            'fields': ('usage_limit', 'usage_limit_per_user', 'times_used')
        }),
        ('Validity', {
            'fields': ('start_date', 'end_date')
        }),
        ('Scope', {
            'fields': ('scope', 'categories', 'seller')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['id', 'coupon', 'user', 'order', 'discount_amount', 'used_at']
    list_filter = ['used_at', 'coupon']
    search_fields = ['user__email', 'coupon__code', 'order__reference']
    readonly_fields = ['used_at']
