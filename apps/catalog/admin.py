from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    Category, ProductType, Attribute, AttributeOption,
    TypeAttributeRule, Product, ProductImage, ProductAttributeValue,
    CategoryTranslation, ProductTypeTranslation, AttributeTranslation,
    AttributeOptionTranslation, ProductTranslation
)


# ============================================================================
# TRANSLATION INLINES
# ============================================================================

class CategoryTranslationInline(admin.TabularInline):
    model = CategoryTranslation
    extra = 1
    fields = ('language_code', 'name', 'description')


class ProductTypeTranslationInline(admin.TabularInline):
    model = ProductTypeTranslation
    extra = 1
    fields = ('language_code', 'name', 'description')


class AttributeTranslationInline(admin.TabularInline):
    model = AttributeTranslation
    extra = 1
    fields = ('language_code', 'name')


class AttributeOptionTranslationInline(admin.TabularInline):
    model = AttributeOptionTranslation
    extra = 1
    fields = ('language_code', 'value')


class ProductTranslationInline(admin.TabularInline):
    model = ProductTranslation
    extra = 1
    fields = ('language_code', 'name', 'description')


# ============================================================================
# MAIN ADMIN CLASSES
# ============================================================================


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CategoryTranslationInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'attribute_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductTypeTranslationInline]

    def attribute_count(self, obj):
        return obj.attribute_rules.count()
    attribute_count.short_description = _('Attributes')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'data_type', 'is_active', 'created_at')
    list_filter = ('data_type', 'is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AttributeTranslationInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AttributeOption)
class AttributeOptionAdmin(admin.ModelAdmin):
    list_display = ('value', 'attribute', 'created_at')
    list_filter = ('attribute', 'created_at')
    search_fields = ('value', 'attribute__name')
    readonly_fields = ('created_at',)
    inlines = [AttributeOptionTranslationInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(TypeAttributeRule)
class TypeAttributeRuleAdmin(admin.ModelAdmin):
    list_display = ('product_type', 'attribute', 'is_required', 'display_order')
    list_filter = ('product_type', 'is_required')
    search_fields = ('product_type__name', 'attribute__name')
    ordering = ('product_type', 'display_order')
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_primary')


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 0
    fields = ('attribute', 'value_text', 'value_number', 'value_bool', 'value_option')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'category', 'status', 'price', 'stock', 'can_publish_status')
    list_filter = ('status', 'product_type', 'category', 'created_at')
    search_fields = ('name', 'seller__shop_name')
    readonly_fields = ('created_at', 'updated_at', 'seller')
    inlines = [ProductImageInline, ProductAttributeValueInline, ProductTranslationInline]
    fieldsets = (
        (_('Product Info'), {'fields': ('seller', 'name', 'description')}),
        (_('Classification'), {'fields': ('category', 'product_type')}),
        (_('Pricing & Inventory'), {'fields': ('price', 'stock')}),
        (_('Status'), {'fields': ('status',)}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def can_publish_status(self, obj):
        if obj.can_be_published():
            return format_html('<span style="color: green;">✓ Ready</span>')
        return format_html('<span style="color: red;">✗ Missing attrs</span>')
    can_publish_status.short_description = _('Publishable')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'seller_profile'):
            return qs.filter(seller=request.user.seller_profile)
        return qs.none()

    def has_add_permission(self, request):
        return request.user.is_superuser or hasattr(request.user, 'seller_profile')

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and hasattr(request.user, 'seller_profile'):
            return obj.seller == request.user.seller_profile
        return False

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            obj.seller = request.user.seller_profile
        super().save_model(request, obj, form, change)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_thumbnail', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    readonly_fields = ('created_at', 'image_preview')

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return '-'
    image_thumbnail.short_description = _('Thumbnail')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" max-width="300" />', obj.image.url)
        return '-'
    image_preview.short_description = _('Preview')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'seller_profile'):
            return qs.filter(product__seller=request.user.seller_profile)
        return qs.none()

    def has_add_permission(self, request):
        return request.user.is_superuser or hasattr(request.user, 'seller_profile')

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and hasattr(request.user, 'seller_profile'):
            return obj.product.seller == request.user.seller_profile
        return False

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('product', 'attribute', 'get_value_display')
    list_filter = ('attribute', 'created_at')
    search_fields = ('product__name', 'attribute__name')
    readonly_fields = ('created_at', 'updated_at')

    def get_value_display(self, obj):
        return str(obj.get_value())
    get_value_display.short_description = _('Value')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'seller_profile'):
            return qs.filter(product__seller=request.user.seller_profile)
        return qs.none()

    def has_add_permission(self, request):
        return request.user.is_superuser or hasattr(request.user, 'seller_profile')

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and hasattr(request.user, 'seller_profile'):
            return obj.product.seller == request.user.seller_profile
        return False

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


# ============================================================================
# TRANSLATION ADMIN CLASSES
# ============================================================================
# Manage translations for catalog content in different languages
# ============================================================================


@admin.register(CategoryTranslation)
class CategoryTranslationAdmin(admin.ModelAdmin):
    list_display = ('category', 'language_code', 'name', 'created_at')
    list_filter = ('language_code', 'created_at')
    search_fields = ('category__name', 'name')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs

    def has_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ProductTypeTranslation)
class ProductTypeTranslationAdmin(admin.ModelAdmin):
    list_display = ('product_type', 'language_code', 'name', 'created_at')
    list_filter = ('language_code', 'created_at')
    search_fields = ('product_type__name', 'name')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs

    def has_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AttributeTranslation)
class AttributeTranslationAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'language_code', 'name', 'created_at')
    list_filter = ('language_code', 'created_at')
    search_fields = ('attribute__name', 'name')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs

    def has_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AttributeOptionTranslation)
class AttributeOptionTranslationAdmin(admin.ModelAdmin):
    list_display = ('option', 'language_code', 'value', 'created_at')
    list_filter = ('language_code', 'created_at')
    search_fields = ('option__value', 'value')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs

    def has_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ProductTranslation)
class ProductTranslationAdmin(admin.ModelAdmin):
    list_display = ('product', 'language_code', 'name', 'created_at')
    list_filter = ('language_code', 'created_at')
    search_fields = ('product__name', 'name')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs

    def has_permission(self, request, obj=None):
        return request.user.is_superuser
