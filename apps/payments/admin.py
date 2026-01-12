"""
Admin configuration for payments app.
"""
from django.contrib import admin
from apps.payments.models import Payment, Refund


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    readonly_fields = ['provider_refund_id', 'status', 'created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'provider', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['provider', 'status', 'currency', 'created_at']
    search_fields = ['order__reference', 'provider_intent_id']
    readonly_fields = ['provider_intent_id', 'provider_charge_id', 'client_secret', 'created_at', 'updated_at', 'paid_at']
    inlines = [RefundInline]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment', 'amount', 'status', 'initiated_by', 'created_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['provider_refund_id', 'created_at', 'updated_at']
