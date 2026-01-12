"""
Admin configuration for orders app.
"""
from django.contrib import admin
from apps.orders.models import Order, OrderItem, SellerOrder


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['seller', 'product', 'title_snapshot', 'price_snapshot', 'quantity', 'line_total']
    can_delete = False


class SellerOrderInline(admin.TabularInline):
    model = SellerOrder
    extra = 0
    readonly_fields = ['seller', 'subtotal', 'created_at']
    fields = ['seller', 'status', 'subtotal', 'tracking_number', 'carrier']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'user', 'status', 'payment_status', 
        'total_amount', 'currency', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'currency', 'created_at']
    search_fields = ['reference', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['reference', 'subtotal', 'total_amount', 'created_at', 'updated_at', 'paid_at']
    inlines = [OrderItemInline, SellerOrderInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('reference', 'user', 'status', 'payment_status')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax', 'shipping_fee', 'discount', 'total_amount', 'currency', 'coupon_code')
        }),
        ('Addresses', {
            'fields': ('shipping_address', 'billing_address'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('customer_note', 'admin_note'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'seller', 'title_snapshot', 'quantity', 'price_snapshot', 'line_total']
    list_filter = ['seller', 'created_at']
    search_fields = ['order__reference', 'title_snapshot', 'seller__shop_name']
    readonly_fields = ['order', 'seller', 'product', 'title_snapshot', 'price_snapshot', 'quantity', 'line_total']


@admin.register(SellerOrder)
class SellerOrderAdmin(admin.ModelAdmin):
    list_display = ['seller', 'order', 'status', 'subtotal', 'tracking_number', 'created_at']
    list_filter = ['status', 'seller', 'created_at']
    search_fields = ['order__reference', 'seller__shop_name', 'tracking_number']
    readonly_fields = ['seller', 'order', 'subtotal', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Info', {
            'fields': ('seller', 'order', 'status', 'subtotal')
        }),
        ('Shipping', {
            'fields': ('tracking_number', 'carrier', 'shipped_at', 'delivered_at')
        }),
        ('Notes', {
            'fields': ('seller_note',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
