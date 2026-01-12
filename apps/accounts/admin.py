from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from .models import User, SellerProfile


class SellerProfileInline(TabularInline):
    """Inline seller profile in User admin"""
    model = SellerProfile
    fk_name = 'user'
    extra = 0
    fields = ('shop_name', 'approval_status', 'city')
    readonly_fields = ('created_at',)


@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    """Modern user admin with Unfold theme"""
    
    list_display = ('email', 'get_full_name_display', 'role_badge', 'status_badge', 'created_at')
    list_filter = ('role', 'account_status', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'id')
    
    fieldsets = (
        (_('Personal Info'), {
            'fields': ('id', 'first_name', 'last_name', 'email', 'username')
        }),
        (_('Contact'), {
            'fields': ('phone_number', 'profile_picture_url', 'biography')
        }),
        (_('Password'), {
            'fields': ('password',),
            'classes': ('collapse',)
        }),
        (_('Role & Status'), {
            'fields': ('role', 'account_status', 'email_verified', 'two_factor_enabled', 'is_staff', 'is_superuser', 'groups')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'last_login', 'deleted_at', 'email_verified_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [SellerProfileInline]
    list_per_page = 20
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        """Super admin sees all users"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs.select_related()
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)
    
    @display(description=_("Full Name"), ordering="first_name")
    def get_full_name_display(self, obj):
        """Display full name or email"""
        full_name = obj.get_full_name()
        return full_name if full_name else obj.email
    
    @display(description=_("Role"), ordering="role")
    def role_badge(self, obj):
        """Display role as badge"""
        colors = {
            'super_admin': '#dc2626',
            'seller': '#2563eb',
            'customer': '#059669',
            'courier': '#7c3aed',
        }
        color = colors.get(obj.role, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    
    @display(description=_("Status"), ordering="status")
    def status_badge(self, obj):
        """Display status as badge"""
        colors = {
            'active': '#10b981',
            'inactive': '#6b7280',
            'suspended': '#f59e0b',
            'banned': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(SellerProfile)
class SellerProfileAdmin(ModelAdmin):
    """Modern seller profile admin"""
    
    list_display = ('shop_name', 'user_email', 'approval_badge', 'seller_level', 'average_rating', 'created_at')
    list_filter = ('approval_status', 'seller_level', 'created_at', 'country')
    search_fields = ('shop_name', 'user__email', 'business_registration_number')
    readonly_fields = ('created_at', 'updated_at', 'user', 'id', 'total_products', 'average_rating', 'total_reviews')
    
    fieldsets = (
        (_('Account'), {
            'fields': ('id', 'user')
        }),
        (_('Shop Information'), {
            'fields': ('shop_name', 'shop_slug', 'shop_description', 'shop_logo_url', 'shop_banner_url')
        }),
        (_('Business Information'), {
            'fields': ('business_type', 'business_registration_number', 'tax_identification_number')
        }),
        (_('Contact Information'), {
            'fields': ('primary_phone', 'secondary_phone', 'support_email')
        }),
        (_('Business Address'), {
            'fields': ('street_address', 'building_number', 'postal_code', 'city', 'state_province', 'country')
        }),
        (_('Approval & Status'), {
            'fields': ('approval_status', 'approved_by', 'approval_note', 'approved_at')
        }),
        (_('Metrics'), {
            'fields': ('total_products', 'average_rating', 'total_reviews', 'total_orders', 'seller_level'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 20
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs.select_related('user', 'approved_by')
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    @display(description=_("User Email"), ordering="user__email")
    def user_email(self, obj):
        return obj.user.email
    
    @display(description=_("Approval Status"), ordering="approval_status")
    def approval_badge(self, obj):
        """Display approval status as badge"""
        colors = {
            'approved': '#10b981',
            'pending': '#f59e0b',
            'suspended': '#ef4444',
            'rejected': '#dc2626',
            'banned': '#7c2d12',
        }
        color = colors.get(obj.approval_status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_approval_status_display()
        )
