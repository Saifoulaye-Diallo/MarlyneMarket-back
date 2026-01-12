"""
Serializers with translation support for multilingual catalog content.
"""

from rest_framework import serializers
from django.conf import settings
from django.utils.translation import get_language_from_request
from .models import (
    Category, ProductType, Attribute, AttributeOption,
    TypeAttributeRule, Product, ProductImage, ProductAttributeValue,
    CategoryTranslation, ProductTypeTranslation, AttributeTranslation,
    AttributeOptionTranslation, ProductTranslation
)
from .i18n import get_translated_name, get_translated_description


class TranslatedCategorySerializer(serializers.ModelSerializer):
    """Category with translation support."""
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'created_at', 'available_languages']
        read_only_fields = ['id', 'created_at', 'slug']

    def get_name(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        return get_translated_name(obj, language)

    def get_description(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        return get_translated_description(obj, language)

    def get_available_languages(self, obj):
        return list(obj.translations.values_list('language_code', flat=True))


class TranslatedAttributeOptionSerializer(serializers.ModelSerializer):
    """Attribute option with translation support."""
    value = serializers.SerializerMethodField()

    class Meta:
        model = AttributeOption
        fields = ['id', 'value', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_value(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        return get_translated_name(obj, language, default_field='value')


class TranslatedAttributeSerializer(serializers.ModelSerializer):
    """Attribute with translation support."""
    name = serializers.SerializerMethodField()
    options = TranslatedAttributeOptionSerializer(many=True, read_only=True)
    available_languages = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = ['id', 'name', 'data_type', 'is_active', 'options', 'created_at', 'available_languages']
        read_only_fields = ['id', 'created_at']

    def get_name(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        return get_translated_name(obj, language)

    def get_available_languages(self, obj):
        return list(obj.translations.values_list('language_code', flat=True))


class TranslatedTypeAttributeRuleSerializer(serializers.ModelSerializer):
    """Type attribute rule with translated attribute info."""
    attribute_name = serializers.SerializerMethodField()
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

    def get_attribute_name(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        return get_translated_name(obj.attribute, language)

    def get_attribute_options(self, obj):
        if obj.attribute.data_type == 'choice':
            context = {'language_code': self.context.get('language_code')}
            return TranslatedAttributeOptionSerializer(
                obj.attribute.options.all(),
                many=True,
                context=context
            ).data
        return []


class TranslatedProductTypeSerializer(serializers.ModelSerializer):
    """Product type with translation support."""
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    attribute_rules = TranslatedTypeAttributeRuleSerializer(many=True, read_only=True)
    available_languages = serializers.SerializerMethodField()

    class Meta:
        model = ProductType
        fields = ['id', 'name', 'description', 'is_active', 'attribute_rules', 'created_at', 'available_languages']
        read_only_fields = ['id', 'created_at']

    def get_name(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        return get_translated_name(obj, language)

    def get_description(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        return get_translated_description(obj, language)

    def get_available_languages(self, obj):
        return list(obj.translations.values_list('language_code', flat=True))


class TranslatedProductTypeSchemaSerializer(serializers.Serializer):
    """Returns translated dynamic form schema for a product type."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()

    def get_name(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        return get_translated_name(obj, language)

    def get_attributes(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        rules = obj.attribute_rules.all()
        attributes = []
        for rule in rules:
            attr_data = {
                'id': rule.attribute.id,
                'name': get_translated_name(rule.attribute, language),
                'data_type': rule.attribute.data_type,
                'is_required': rule.is_required,
                'display_order': rule.display_order,
            }
            if rule.attribute.data_type == 'choice':
                context = {'language_code': language}
                attr_data['options'] = TranslatedAttributeOptionSerializer(
                    rule.attribute.options.all(),
                    many=True,
                    context=context
                ).data
            attributes.append(attr_data)
        return sorted(attributes, key=lambda x: x['display_order'])

    def get_available_languages(self, obj):
        return list(obj.translations.values_list('language_code', flat=True))


class TranslatedProductSerializer(serializers.ModelSerializer):
    """Product with translation support."""
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    product_type_name = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'category', 'category_name', 'product_type',
            'product_type_name', 'name', 'description', 'price', 'stock',
            'status', 'images', 'created_at', 'updated_at', 'available_languages'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'seller']

    def get_name(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        return get_translated_name(obj, language)

    def get_description(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        return get_translated_description(obj, language)

    def get_category_name(self, obj):
        if obj.category:
            language = self.context.get('language_code', settings.LANGUAGE_CODE)
            return get_translated_name(obj.category, language)
        return None

    def get_product_type_name(self, obj):
        language = self.context.get('language_code', settings.LANGUAGE_CODE)
        return get_translated_name(obj.product_type, language)

    def get_images(self, obj):
        return [
            {
                'id': img.id,
                'image': img.image.url if img.image else None,
                'is_primary': img.is_primary,
            }
            for img in obj.images.all()
        ]

    def get_available_languages(self, obj):
        return list(obj.translations.values_list('language_code', flat=True))
