from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
import os
from .models import (
    Category, ProductType, Attribute, AttributeOption,
    TypeAttributeRule, Product, ProductImage, ProductAttributeValue,
    CategoryTranslation, ProductTypeTranslation, AttributeTranslation,
    AttributeOptionTranslation, ProductTranslation
)


class CategoryTranslationSerializer(serializers.ModelSerializer):
    """Serializer for category translations"""
    
    class Meta:
        model = CategoryTranslation
        fields = ['id', 'language_code', 'name', 'description', 'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for categories with translations"""
    
    translations = CategoryTranslationSerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'is_active',
            'product_count', 'created_at', 'updated_at', 'translations'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_product_count(self, obj):
        return obj.products.filter(status='published').count()


class AttributeOptionTranslationSerializer(serializers.ModelSerializer):
    """Serializer for attribute option translations"""
    
    class Meta:
        model = AttributeOptionTranslation
        fields = ['id', 'language_code', 'value', 'created_at', 'updated_at']


class AttributeOptionSerializer(serializers.ModelSerializer):
    """Serializer for attribute options"""
    
    translations = AttributeOptionTranslationSerializer(many=True, read_only=True)
    
    class Meta:
        model = AttributeOption
        fields = ['id', 'attribute', 'value', 'created_at', 'translations']
        read_only_fields = ['id', 'created_at']


class AttributeTranslationSerializer(serializers.ModelSerializer):
    """Serializer for attribute translations"""
    
    class Meta:
        model = AttributeTranslation
        fields = ['id', 'language_code', 'name', 'created_at', 'updated_at']


class AttributeSerializer(serializers.ModelSerializer):
    """Serializer for attributes"""
    
    options = AttributeOptionSerializer(many=True, read_only=True)
    translations = AttributeTranslationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Attribute
        fields = [
            'id', 'name', 'data_type', 'is_active',
            'created_at', 'updated_at', 'options', 'translations'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TypeAttributeRuleSerializer(serializers.ModelSerializer):
    """Serializer for type attribute rules"""
    
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    attribute_data_type = serializers.CharField(source='attribute.data_type', read_only=True)
    
    class Meta:
        model = TypeAttributeRule
        fields = [
            'id', 'product_type', 'attribute', 'attribute_name',
            'attribute_data_type', 'is_required', 'display_order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductTypeTranslationSerializer(serializers.ModelSerializer):
    """Serializer for product type translations"""
    
    class Meta:
        model = ProductTypeTranslation
        fields = ['id', 'language_code', 'name', 'description', 'created_at', 'updated_at']


class ProductTypeSerializer(serializers.ModelSerializer):
    """Serializer for product types"""
    
    attribute_rules = TypeAttributeRuleSerializer(many=True, read_only=True)
    translations = ProductTypeTranslationSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductType
        fields = [
            'id', 'name', 'description', 'is_active',
            'created_at', 'updated_at', 'attribute_rules', 'translations'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images with validation"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'image_url', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at', 'image_url']
        
    def get_image_url(self, obj):
        """Return full URL of the image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
        
    def validate_image(self, value):
        """Validate uploaded image file"""
        if value:
            # Check file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            extension = os.path.splitext(value.name)[1].lower()
            if extension not in valid_extensions:
                raise serializers.ValidationError(
                    f'Invalid file format. Allowed formats: {", ".join(valid_extensions)}'
                )
            
            # Check file size (5MB max)
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError(
                    f'File size must be less than {max_size // (1024 * 1024)}MB'
                )
                
        return value


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    """Serializer for product attribute values"""
    
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    attribute_type = serializers.CharField(source='attribute.data_type', read_only=True)
    
    class Meta:
        model = ProductAttributeValue
        fields = [
            'id', 'product', 'attribute', 'attribute_name', 'attribute_type',
            'value_text', 'value_number', 'value_bool', 'value_option',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductTranslationSerializer(serializers.ModelSerializer):
    """Serializer for product translations"""
    
    class Meta:
        model = ProductTranslation
        fields = ['id', 'language_code', 'name', 'description', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products with all fields and relationships"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    product_type_name = serializers.CharField(source='product_type.name', read_only=True)
    seller_shop_name = serializers.CharField(source='seller.shop_name', read_only=True)
    
    images = ProductImageSerializer(many=True, read_only=True)
    attribute_values = ProductAttributeValueSerializer(many=True, read_only=True)
    translations = ProductTranslationSerializer(many=True, read_only=True)
    
    effective_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'seller_shop_name', 'category', 'category_name',
            'product_type', 'product_type_name', 'name', 'slug', 'description',
            'short_description', 'price', 'cost_price', 'discount_price',
            'discount_percentage', 'effective_price', 'stock', 'minimum_stock',
            'status', 'condition', 'shipping_type', 'shipping_weight',
            'shipping_cost', 'sku', 'upc_ean', 'average_rating',
            'total_reviews', 'total_sold', 'is_featured', 'is_on_sale',
            'is_digital', 'meta_title', 'meta_description', 'meta_keywords',
            'published_at', 'expires_at', 'created_at', 'updated_at',
            'images', 'attribute_values', 'translations'
        ]
        read_only_fields = [
            'id', 'average_rating', 'total_reviews', 'total_sold',
            'created_at', 'updated_at'
        ]
    
    def get_effective_price(self, obj):
        return float(obj.get_effective_price())


class AttributeSerializer(serializers.ModelSerializer):
    options = AttributeOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = ['id', 'name', 'data_type', 'is_active', 'options', 'created_at']
        read_only_fields = ['id', 'created_at']


class TypeAttributeRuleSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    attribute_data_type = serializers.CharField(source='attribute.data_type', read_only=True)
    attribute_options = serializers.SerializerMethodField()

    class Meta:
        model = TypeAttributeRule
        fields = [
            'id', 'product_type', 'attribute', 'attribute_name',
            'attribute_data_type', 'attribute_options', 'is_required',
            'display_order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_attribute_options(self, obj):
        if obj.attribute.data_type == 'choice':
            return AttributeOptionSerializer(
                obj.attribute.options.all(),
                many=True
            ).data
        return []


class ProductTypeSerializer(serializers.ModelSerializer):
    attribute_rules = TypeAttributeRuleSerializer(many=True, read_only=True)

    class Meta:
        model = ProductType
        fields = ['id', 'name', 'description', 'is_active', 'attribute_rules', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductTypeSchemaSerializer(serializers.Serializer):
    """Returns dynamic form schema for a product type."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    attributes = serializers.SerializerMethodField()

    def get_attributes(self, obj):
        rules = obj.attribute_rules.all()
        attributes = []
        for rule in rules:
            attr_data = {
                'id': rule.attribute.id,
                'name': rule.attribute.name,
                'data_type': rule.attribute.data_type,
                'is_required': rule.is_required,
                'display_order': rule.display_order,
            }
            if rule.attribute.data_type == 'choice':
                attr_data['options'] = AttributeOptionSerializer(
                    rule.attribute.options.all(),
                    many=True
                ).data
            attributes.append(attr_data)
        return sorted(attributes, key=lambda x: x['display_order'])


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    attribute_data_type = serializers.CharField(source='attribute.data_type', read_only=True)
    value = serializers.SerializerMethodField()

    class Meta:
        model = ProductAttributeValue
        fields = [
            'id', 'product', 'attribute', 'attribute_name',
            'attribute_data_type', 'value_text', 'value_number',
            'value_bool', 'value_option', 'value'
        ]

    def get_value(self, obj):
        val = obj.get_value()
        if isinstance(val, AttributeOption):
            return AttributeOptionSerializer(val).data
        return val

    def validate(self, attrs):
        attribute = attrs.get('attribute')
        if attribute.data_type == 'text' and not attrs.get('value_text'):
            raise serializers.ValidationError('value_text is required for text attributes')
        elif attribute.data_type == 'number' and attrs.get('value_number') is None:
            raise serializers.ValidationError('value_number is required for number attributes')
        elif attribute.data_type == 'bool' and attrs.get('value_bool') is None:
            raise serializers.ValidationError('value_bool is required for boolean attributes')
        elif attribute.data_type == 'choice' and not attrs.get('value_option'):
            raise serializers.ValidationError('value_option is required for choice attributes')
        return attrs


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.shop_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'seller_name', 'name', 'category_name', 'product_type',
            'price', 'discount_price', 'discount_percentage', 'cost_price',
            'stock', 'minimum_stock', 'status', 'condition',
            'shipping_type', 'shipping_weight', 'shipping_cost',
            'sku', 'upc_ean', 'average_rating', 'total_reviews', 'total_sold',
            'is_featured', 'is_on_sale', 'is_digital',
            'short_description', 'description',
            'meta_title', 'meta_description', 'meta_keywords',
            'created_at', 'published_at', 'expires_at', 'primary_image'
        ]
        read_only_fields = ['id', 'created_at', 'published_at', 'expires_at']

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return ProductImageSerializer(primary).data
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.shop_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    attribute_values = ProductAttributeValueSerializer(many=True, read_only=True)
    can_be_published = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'seller_name', 'category', 'category_name',
            'product_type', 'name', 'description', 'price', 'stock', 'status',
            'images', 'attribute_values', 'can_be_published', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'seller', 'created_at', 'updated_at']

    def get_can_be_published(self, obj):
        return obj.can_be_published()

    def validate(self, attrs):
        try:
            product = Product(**attrs)
            product.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))
        return attrs

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than 0')
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError('Stock cannot be negative')
        return value


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'category', 'product_type', 'name', 'description', 'price', 'stock', 'status']
        read_only_fields = ['id']

    def validate_status(self, value):
        if value == 'published':
            product = self.instance or Product(**self.initial_data)
            if not product.product_type_id:
                raise serializers.ValidationError('Product type is required')
        return value

    def validate(self, attrs):
        try:
            # Check if instance exists to validate properly
            if self.instance:
                for attr, value in attrs.items():
                    setattr(self.instance, attr, value)
                self.instance.full_clean()
            else:
                product = Product(**attrs)
                product.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))
        return attrs
