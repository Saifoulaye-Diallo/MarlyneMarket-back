"""
Admin configuration for returns app.
"""
from django.contrib import admin
from apps.returns.models import ReturnRequest


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_item', 'user', 'reason', 'status', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['order_item__order__reference', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'responded_at']
