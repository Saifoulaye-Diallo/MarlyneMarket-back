from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.accounts.models import SellerProfile


class Category(models.Model):
    """
    Product categories. Multi-language support with translatable name.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('Category Name')
    )
    slug = models.SlugField(
        unique=True,
        verbose_name=_('Slug')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductType(models.Model):
    """
    Product type defines the structure of products.
    Each product must belong to a specific product type.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('Product Type Name')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product Type')
        verbose_name_plural = _('Product Types')
        ordering = ['name']

    def __str__(self):
        return self.name


class Attribute(models.Model):
    """
    Attributes define dynamic product properties.
    Supports text, number, boolean, and choice data types.
    """
    DATA_TYPE_CHOICES = [
        ('text', _('Text')),
        ('number', _('Number')),
        ('bool', _('Boolean')),
        ('choice', _('Choice')),
    ]

    name = models.CharField(
        max_length=255,
        verbose_name=_('Attribute Name')
    )
    data_type = models.CharField(
        max_length=20,
        choices=DATA_TYPE_CHOICES,
        default='text',
        verbose_name=_('Data Type')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')
        ordering = ['name']
        unique_together = ['name', 'data_type']

    def __str__(self):
        return f"{self.name} ({self.get_data_type_display()})"


class AttributeOption(models.Model):
    """
    Predefined options for choice-type attributes.
    """
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name='options',
        limit_choices_to={'data_type': 'choice'}
    )
    value = models.CharField(
        max_length=255,
        verbose_name=_('Option Value')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Attribute Option')
        verbose_name_plural = _('Attribute Options')
        ordering = ['created_at']
        unique_together = ['attribute', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class TypeAttributeRule(models.Model):
    """
    Defines which attributes are required/optional for each product type.
    Controls the dynamic form schema for products.
    """
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.CASCADE,
        related_name='attribute_rules'
    )
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name='type_rules'
    )
    is_required = models.BooleanField(
        default=False,
        verbose_name=_('Required')
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name=_('Display Order')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Type Attribute Rule')
        verbose_name_plural = _('Type Attribute Rules')
        ordering = ['display_order']
        unique_together = ['product_type', 'attribute']

    def __str__(self):
        return f"{self.product_type.name} - {self.attribute.name}"


class Product(models.Model):
    """
    Main product model. Belongs to a seller and has dynamic attributes based on its type.
    """
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('disabled', _('Disabled')),
    ]
    
    CONDITION_CHOICES = [
        ('new', _('New')),
        ('like_new', _('Like New')),
        ('used', _('Used')),
        ('refurbished', _('Refurbished')),
    ]
    
    SHIPPING_CHOICES = [
        ('standard', _('Standard Shipping')),
        ('express', _('Express Shipping')),
        ('free', _('Free Shipping')),
        ('custom', _('Custom Shipping')),
    ]

    seller = models.ForeignKey(
        SellerProfile,
        on_delete=models.CASCADE,
        related_name='products'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        related_name='products'
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Product Name')
    )
    slug = models.SlugField(
        unique=True,
        verbose_name=_('Slug'),
        blank=True,
        null=True
    )
    description = models.TextField(
        verbose_name=_('Description')
    )
    short_description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Short Description')
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Price')
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Cost Price')
    )
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Discount Price')
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_('Discount Percentage')
    )
    stock = models.IntegerField(
        default=0,
        verbose_name=_('Stock')
    )
    minimum_stock = models.IntegerField(
        default=5,
        verbose_name=_('Minimum Stock Alert')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status')
    )
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='new',
        verbose_name=_('Condition')
    )
    shipping_type = models.CharField(
        max_length=20,
        choices=SHIPPING_CHOICES,
        default='standard',
        verbose_name=_('Shipping Type')
    )
    shipping_weight = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name=_('Weight (kg)')
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Shipping Cost')
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('SKU'),
        blank=True,
        null=True
    )
    upc_ean = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('UPC/EAN')
    )
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name=_('Average Rating')
    )
    total_reviews = models.IntegerField(
        default=0,
        verbose_name=_('Total Reviews')
    )
    total_sold = models.IntegerField(
        default=0,
        verbose_name=_('Total Sold')
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_('Featured Product')
    )
    is_on_sale = models.BooleanField(
        default=False,
        verbose_name=_('On Sale')
    )
    is_digital = models.BooleanField(
        default=False,
        verbose_name=_('Digital Product')
    )
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Meta Title')
    )
    meta_description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Meta Description')
    )
    meta_keywords = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Meta Keywords')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Published At')
    )
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Expiration Date')
    )

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['product_type']),
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['published_at']),
            models.Index(fields=['average_rating', 'total_reviews']),
        ]

    def __str__(self):
        return f"{self.name} ({self.seller.shop_name})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.price <= 0:
            raise ValidationError(_('Price must be greater than 0'))
        if self.stock < 0:
            raise ValidationError(_('Stock cannot be negative'))
        if self.cost_price and self.cost_price > self.price:
            raise ValidationError(_('Cost price cannot be greater than selling price'))
        if self.discount_percentage < 0 or self.discount_percentage > 100:
            raise ValidationError(_('Discount percentage must be between 0 and 100'))

    def can_be_published(self):
        """Check if product has all required attributes before publishing."""
        required_rules = self.product_type.attribute_rules.filter(is_required=True)
        for rule in required_rules:
            if not ProductAttributeValue.objects.filter(
                product=self,
                attribute=rule.attribute
            ).exists():
                return False
        return True
    
    def get_effective_price(self):
        """Return the effective price considering discounts."""
        if self.discount_price:
            return self.discount_price
        if self.discount_percentage > 0:
            return self.price * (1 - self.discount_percentage / 100)
        return self.price


class ProductImage(models.Model):
    """
    Product images. Supports multiple images per product with a primary image indicator.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='products/%Y/%m/%d/',
        verbose_name=_('Image')
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name=_('Primary Image')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')
        ordering = ['-is_primary', 'created_at']

    def __str__(self):
        return f"{self.product.name} - Image"

    def save(self, *args, **kwargs):
        """Ensure only one primary image per product."""
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductAttributeValue(models.Model):
    """
    Dynamic attribute values for products.
    Stores the actual values of attributes selected for a product.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='attribute_values'
    )
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE
    )
    value_text = models.TextField(
        blank=True,
        null=True
    )
    value_number = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    value_bool = models.BooleanField(
        blank=True,
        null=True
    )
    value_option = models.ForeignKey(
        AttributeOption,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product Attribute Value')
        verbose_name_plural = _('Product Attribute Values')
        unique_together = ['product', 'attribute']
        ordering = ['attribute__name']

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}"

    def get_value(self):
        """Return the actual value based on attribute data type."""
        if self.attribute.data_type == 'text':
            return self.value_text
        elif self.attribute.data_type == 'number':
            return self.value_number
        elif self.attribute.data_type == 'bool':
            return self.value_bool
        elif self.attribute.data_type == 'choice':
            return self.value_option
        return None


# ============================================================================
# TRANSLATION MODELS (Option A: Explicit Translation Tables)
# ============================================================================
# These models store translations for content in different languages.
# Supports: en, fr, es, ar (expandable to 8+ languages)
# ============================================================================


class CategoryTranslation(models.Model):
    """
    Stores translated content for categories.
    Allows categories to have different names and descriptions per language.
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='translations'
    )
    language_code = models.CharField(
        max_length=5,
        choices=[(code, name) for code, name in settings.LANGUAGES]
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Category Name')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Category Translation')
        verbose_name_plural = _('Category Translations')
        unique_together = ['category', 'language_code']
        indexes = [
            models.Index(fields=['category', 'language_code']),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.get_language_code_display()}"


class ProductTypeTranslation(models.Model):
    """
    Stores translated content for product types.
    """
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.CASCADE,
        related_name='translations'
    )
    language_code = models.CharField(
        max_length=5,
        choices=[(code, name) for code, name in settings.LANGUAGES]
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Product Type Name')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product Type Translation')
        verbose_name_plural = _('Product Type Translations')
        unique_together = ['product_type', 'language_code']
        indexes = [
            models.Index(fields=['product_type', 'language_code']),
        ]

    def __str__(self):
        return f"{self.product_type.name} - {self.get_language_code_display()}"


class AttributeTranslation(models.Model):
    """
    Stores translated content for attributes.
    """
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name='translations'
    )
    language_code = models.CharField(
        max_length=5,
        choices=[(code, name) for code, name in settings.LANGUAGES]
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Attribute Name')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Attribute Translation')
        verbose_name_plural = _('Attribute Translations')
        unique_together = ['attribute', 'language_code']
        indexes = [
            models.Index(fields=['attribute', 'language_code']),
        ]

    def __str__(self):
        return f"{self.attribute.name} - {self.get_language_code_display()}"


class AttributeOptionTranslation(models.Model):
    """
    Stores translated content for attribute options.
    """
    option = models.ForeignKey(
        AttributeOption,
        on_delete=models.CASCADE,
        related_name='translations'
    )
    language_code = models.CharField(
        max_length=5,
        choices=[(code, name) for code, name in settings.LANGUAGES]
    )
    value = models.CharField(
        max_length=255,
        verbose_name=_('Option Value')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Attribute Option Translation')
        verbose_name_plural = _('Attribute Option Translations')
        unique_together = ['option', 'language_code']
        indexes = [
            models.Index(fields=['option', 'language_code']),
        ]

    def __str__(self):
        return f"{self.option.value} - {self.get_language_code_display()}"


class ProductTranslation(models.Model):
    """
    Stores translated content for products.
    Allows sellers to sell same product with different descriptions per language.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='translations'
    )
    language_code = models.CharField(
        max_length=5,
        choices=[(code, name) for code, name in settings.LANGUAGES]
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Product Name')
    )
    description = models.TextField(
        verbose_name=_('Description')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product Translation')
        verbose_name_plural = _('Product Translations')
        unique_together = ['product', 'language_code']
        indexes = [
            models.Index(fields=['product', 'language_code']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.get_language_code_display()}"
