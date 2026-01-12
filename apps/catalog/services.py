"""
Business logic services for catalog operations.

This module centralizes complex business rules to keep them:
- Testable
- Reusable across views/serializers
- Maintainable
- Separated from API concerns
"""
import os
import re
from typing import Dict, Optional, Any

from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _
import cloudinary
import cloudinary.uploader

from .models import (
    Product, ProductImage, ProductAttributeValue, AttributeOption,
    CategoryTranslation, ProductTypeTranslation, AttributeTranslation,
    AttributeOptionTranslation, ProductTranslation
)


def get_translated_content(obj, field_name, language_code=None):
    """
    Get translated content for an object.
    
    Falls back to DEFAULT_LANGUAGE if translation not found.
    
    Args:
        obj: The model instance (Category, ProductType, Attribute, Product)
        field_name: The field to get (e.g., 'name', 'description')
        language_code: Target language (default: settings.LANGUAGE_CODE)
    
    Returns:
        Translated value or default value
    """
    if language_code is None:
        language_code = settings.LANGUAGE_CODE
    
    # Get translation model based on object type
    translation_models = {
        'Category': (CategoryTranslation, 'category'),
        'ProductType': (ProductTypeTranslation, 'product_type'),
        'Attribute': (AttributeTranslation, 'attribute'),
        'Product': (ProductTranslation, 'product'),
    }
    
    model_name = obj.__class__.__name__
    if model_name not in translation_models:
        return getattr(obj, field_name, None)
    
    trans_model, obj_field = translation_models[model_name]
    
    try:
        translation = trans_model.objects.get(
            **{obj_field: obj, 'language_code': language_code}
        )
        return getattr(translation, field_name)
    except trans_model.DoesNotExist:
        # Fallback to default language
        if language_code != settings.LANGUAGE_CODE:
            try:
                translation = trans_model.objects.get(
                    **{obj_field: obj, 'language_code': settings.LANGUAGE_CODE}
                )
                return getattr(translation, field_name)
            except trans_model.DoesNotExist:
                pass
        
        # Final fallback to base model
        return getattr(obj, field_name, None)


def set_translated_content(obj, updates, language_code):
    """
    Set translated content for an object.
    
    Args:
        obj: The model instance to translate
        updates: Dict of {field_name: value} to translate
        language_code: Target language code
    
    Raises:
        ValidationError: If language_code is invalid
    """
    valid_languages = [code for code, _ in settings.LANGUAGES]
    if language_code not in valid_languages:
        raise ValidationError(
            _('Invalid language code. Valid codes: %(codes)s') 
            % {'codes': ', '.join(valid_languages)}
        )
    
    model_name = obj.__class__.__name__
    translation_models = {
        'Category': (CategoryTranslation, 'category'),
        'ProductType': (ProductTypeTranslation, 'product_type'),
        'Attribute': (AttributeTranslation, 'attribute'),
        'Product': (ProductTranslation, 'product'),
    }
    
    if model_name not in translation_models:
        raise ValidationError(_('Translation not supported for %(model)s') % {'model': model_name})
    
    trans_model, obj_field = translation_models[model_name]
    
    # Get or create translation
    translation, created = trans_model.objects.get_or_create(
        **{obj_field: obj, 'language_code': language_code}
    )
    
    # Update fields
    for field, value in updates.items():
        if hasattr(translation, field):
            setattr(translation, field, value)
    
    translation.save()
    return translation


def validate_required_attributes(product):
    """
    Check if product has all required attributes for its type.
    
    Args:
        product: Product instance
    
    Returns:
        tuple: (is_valid, missing_attributes_list)
    """
    required_rules = product.product_type.attribute_rules.filter(is_required=True)
    missing = []
    
    for rule in required_rules:
        if not ProductAttributeValue.objects.filter(
            product=product,
            attribute=rule.attribute
        ).exists():
            missing.append(rule.attribute.name)
    
    return len(missing) == 0, missing


def publish_product(product):
    """
    Publish a product.
    
    Verifies all required attributes are set before publishing.
    
    Args:
        product: Product instance to publish
    
    Returns:
        Product: Updated product instance
    
    Raises:
        ValidationError: If required attributes are missing
    """
    is_valid, missing = validate_required_attributes(product)
    
    if not is_valid:
        raise ValidationError(
            _('Cannot publish product. Missing required attributes: %(attrs)s')
            % {'attrs': ', '.join(missing)}
        )
    
    product.status = 'published'
    product.save()
    return product


def set_product_attribute_values(product, attribute_values_data):
    """
    Set/update product attribute values.
    
    Validates data types match attribute definitions.
    
    Args:
        product: Product instance
        attribute_values_data: Dict of {attribute_id: value}
    
    Returns:
        list: Created/updated ProductAttributeValue instances
    
    Raises:
        ValidationError: If attribute not found or data type mismatch
    """
    from .models import Attribute
    
    result = []
    
    for attr_id, value in attribute_values_data.items():
        try:
            attribute = Attribute.objects.get(id=attr_id)
        except Attribute.DoesNotExist:
            raise ValidationError(
                _('Attribute with id %(id)s does not exist') % {'id': attr_id}
            )
        
        # Validate and create/update attribute value
        attr_value, created = ProductAttributeValue.objects.get_or_create(
            product=product,
            attribute=attribute
        )
        
        # Set value based on attribute data type
        if attribute.data_type == 'text':
            attr_value.value_text = str(value) if value is not None else None
        elif attribute.data_type == 'number':
            try:
                attr_value.value_number = float(value) if value is not None else None
            except (ValueError, TypeError):
                raise ValidationError(
                    _('Attribute %(attr)s requires a numeric value')
                    % {'attr': attribute.name}
                )
        elif attribute.data_type == 'bool':
            attr_value.value_bool = bool(value) if value is not None else None
        elif attribute.data_type == 'choice':
            if value is not None:
                try:
                    attr_value.value_option = AttributeOption.objects.get(id=value)
                except AttributeOption.DoesNotExist:
                    raise ValidationError(
                        _('Invalid option %(id)s for attribute %(attr)s')
                        % {'id': value, 'attr': attribute.name}
                    )
            else:
                attr_value.value_option = None
        
        attr_value.save()
        result.append(attr_value)
    
    return result


@transaction.atomic
def ensure_single_primary_image(product):
    """
    Ensure product has exactly one primary image.
    
    If no primary image exists, sets the first image as primary.
    If multiple primary images exist, keeps only the most recent.
    
    Args:
        product: Product instance
    
    Returns:
        ProductImage: The primary image, or None if no images exist
    """
    images = ProductImage.objects.filter(product=product).order_by('-created_at')
    
    if not images.exists():
        return None
    
    # Remove all primary flags
    images.update(is_primary=False)
    
    # Set most recent as primary
    primary = images.first()
    primary.is_primary = True
    primary.save()
    
    return primary


def disable_product(product, reason=None):
    """
    Disable a product (soft delete).
    
    Args:
        product: Product instance
        reason: Optional reason for disabling
    
    Returns:
        Product: Updated product instance
    """
    product.status = 'disabled'
    product.save()
    # Note: Could extend with DisabledProduct model to track reason/timestamp
    return product


def can_seller_manage_product(seller_profile, product):
    """
    Check if seller can manage (view/edit/delete) a product.
    
    Args:
        seller_profile: SellerProfile instance
        product: Product instance
    
    Returns:
        bool: True if seller owns the product
    """
    return product.seller_id == seller_profile.id


def can_seller_manage_image(seller_profile, image):
    """
    Check if seller can manage a product image.
    
    Args:
        seller_profile: SellerProfile instance
        image: ProductImage instance
    
    Returns:
        bool: True if seller owns the image's product
    """
    return image.product.seller_id == seller_profile.id


def get_product_schema(product_type, language_code=None):
    """
    Get the dynamic form schema for a product type.
    
    Used by frontend to generate dynamic forms.
    
    Args:
        product_type: ProductType instance
        language_code: Target language for attribute names
    
    Returns:
        dict: Schema with attributes, requirements, data types, options
    """
    if language_code is None:
        language_code = settings.LANGUAGE_CODE
    
    rules = product_type.attribute_rules.all().order_by('display_order')
    schema = {
        'product_type_id': product_type.id,
        'product_type_name': get_translated_content(product_type, 'name', language_code),
        'attributes': []
    }
    
    for rule in rules:
        attribute = rule.attribute
        attr_schema = {
            'id': attribute.id,
            'name': get_translated_content(attribute, 'name', language_code),
            'data_type': attribute.data_type,
            'is_required': rule.is_required,
            'display_order': rule.display_order,
        }
        
        # Include options for choice attributes
        if attribute.data_type == 'choice':
            options = attribute.options.all()
            attr_schema['options'] = [
                {
                    'id': opt.id,
                    'value': get_translated_content(opt, 'value', language_code)
                }
                for opt in options
            ]
        
        schema['attributes'].append(attr_schema)
    
    return schema


class CloudinaryImageService:
    """Service class for Cloudinary image operations."""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    
    # Maximum file size in bytes (5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    @classmethod
    def validate_image_file(cls, uploaded_file: UploadedFile) -> None:
        """
        Validate uploaded image file.
        
        Args:
            uploaded_file: The uploaded file to validate
            
        Raises:
            ValueError: If file is invalid
        """
        # Check file size
        if uploaded_file.size > cls.MAX_FILE_SIZE:
            raise ValueError(
                f'File size too large. Maximum allowed size is {cls.MAX_FILE_SIZE // (1024*1024)}MB.'
            )
        
        # Check file extension
        if hasattr(uploaded_file, 'name') and uploaded_file.name:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension not in cls.ALLOWED_EXTENSIONS:
                raise ValueError(
                    f'Invalid file type. Allowed types: {", ".join(cls.ALLOWED_EXTENSIONS)}'
                )
        
        # Check content type
        if uploaded_file.content_type:
            allowed_content_types = {
                'image/jpeg', 'image/jpg', 'image/png', 'image/webp'
            }
            if uploaded_file.content_type not in allowed_content_types:
                raise ValueError(f'Invalid file type. Content-Type: {uploaded_file.content_type}')
    
    @classmethod
    def generate_upload_options(cls, product_id: str) -> Dict[str, Any]:
        """
        Generate upload options for Cloudinary.
        
        Args:
            product_id: Product identifier for organizing uploads
            
        Returns:
            Dictionary of upload options
        """
        return {
            'folder': 'marketplace/products',
            'use_filename': True,
            'unique_filename': True,
            'overwrite': False,
            'resource_type': 'image',
            'allowed_formats': list(cls.ALLOWED_EXTENSIONS),
            'transformation': [
                {'quality': 'auto'},
                {'fetch_format': 'auto'}
            ]
        }
    
    @classmethod
    def upload_image(cls, uploaded_file: UploadedFile, product_id: str) -> Dict[str, Any]:
        """
        Upload image to Cloudinary.
        
        Args:
            uploaded_file: The image file to upload
            product_id: Product identifier for organizing uploads
            
        Returns:
            Cloudinary upload response
            
        Raises:
            Exception: If upload fails
        """
        try:
            # Validate file first
            cls.validate_image_file(uploaded_file)
            
            # Generate upload options
            upload_options = cls.generate_upload_options(product_id)
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                uploaded_file,
                **upload_options
            )
            
            return result
            
        except Exception as e:
            raise Exception(f'Failed to upload image to Cloudinary: {str(e)}')
    
    @classmethod
    def delete_image(cls, public_id: str) -> Dict[str, Any]:
        """
        Delete image from Cloudinary.
        
        Args:
            public_id: Cloudinary public ID of the image to delete
            
        Returns:
            Cloudinary deletion response
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result
        except Exception as e:
            # Log error but don't fail completely
            print(f'Warning: Failed to delete image from Cloudinary: {str(e)}')
            return {'result': 'error', 'error': str(e)}
    
    @classmethod
    def extract_public_id_from_url(cls, cloudinary_url: str) -> Optional[str]:
        """
        Extract public_id from Cloudinary URL.
        
        Args:
            cloudinary_url: Full Cloudinary URL
            
        Returns:
            Public ID or None if extraction fails
        """
        try:
            # Pattern to match Cloudinary URLs
            # https://res.cloudinary.com/cloud_name/image/upload/v1234567890/folder/filename.ext
            pattern = r'https://res\.cloudinary\.com/[^/]+/image/upload/(?:v\d+/)?(.+)\.(?:jpg|jpeg|png|webp)$'
            match = re.search(pattern, cloudinary_url)
            
            if match:
                return match.group(1)
            
            return None
        except Exception:
            return None
    
    @classmethod
    def get_image_url(cls, public_id: str, transformations: Optional[list] = None) -> str:
        """
        Generate Cloudinary URL for image.
        
        Args:
            public_id: Cloudinary public ID
            transformations: Optional list of transformations
            
        Returns:
            Cloudinary URL
        """
        try:
            if transformations:
                url, _ = cloudinary.utils.cloudinary_url(
                    public_id,
                    transformation=transformations,
                    secure=True
                )
            else:
                url, _ = cloudinary.utils.cloudinary_url(
                    public_id,
                    secure=True
                )
            return url
        except Exception:
            return ''
    
    @classmethod
    def get_optimized_image_url(
        cls, 
        public_id: str, 
        width: Optional[int] = None,
        height: Optional[int] = None,
        quality: str = 'auto'
    ) -> str:
        """
        Generate optimized image URL with transformations.
        
        Args:
            public_id: Cloudinary public ID
            width: Target width
            height: Target height
            quality: Image quality setting
            
        Returns:
            Optimized Cloudinary URL
        """
        transformations = [
            {'quality': quality},
            {'fetch_format': 'auto'}
        ]
        
        if width or height:
            crop_params = {}
            if width:
                crop_params['width'] = width
            if height:
                crop_params['height'] = height
            crop_params['crop'] = 'fit'
            transformations.append(crop_params)
        
        return cls.get_image_url(public_id, transformations)
