"""
i18n utilities for returning translated catalog content based on Accept-Language header.
"""

from django.conf import settings
from django.utils.translation import get_language_from_request


def get_language_code(request):
    """
    Get the language code from the request.
    Falls back to DEFAULT_LANGUAGE if not supported.
    """
    lang = get_language_from_request(request)
    if lang not in dict(settings.LANGUAGES):
        lang = settings.LANGUAGE_CODE
    return lang


def get_translated_name(obj, language_code, default_field='name'):
    """
    Get translated name/label for catalog objects.
    
    Args:
        obj: Category, ProductType, Attribute, or AttributeOption instance
        language_code: Language code (e.g., 'en', 'fr', 'ar')
        default_field: Field name to use as fallback (default='name')
    
    Returns:
        Translated text or fallback to default language
    """
    if not language_code:
        language_code = settings.LANGUAGE_CODE
    
    # Get translation model name based on object type
    obj_type = type(obj).__name__
    
    if obj_type == 'Category':
        translation_model = obj.translations
        trans_field = 'name'
    elif obj_type == 'ProductType':
        translation_model = obj.translations
        trans_field = 'name'
    elif obj_type == 'Attribute':
        translation_model = obj.translations
        trans_field = 'name'
    elif obj_type == 'AttributeOption':
        translation_model = obj.translations
        trans_field = 'value'
    elif obj_type == 'Product':
        translation_model = obj.translations
        trans_field = 'name'
    else:
        return getattr(obj, default_field, str(obj))
    
    try:
        translation = translation_model.get(language_code=language_code)
        return getattr(translation, trans_field)
    except:
        # Fall back to default language
        if language_code != settings.LANGUAGE_CODE:
            try:
                translation = translation_model.get(language_code=settings.LANGUAGE_CODE)
                return getattr(translation, trans_field)
            except:
                pass
        # Fall back to original field
        return getattr(obj, default_field, str(obj))


def get_translated_description(obj, language_code):
    """
    Get translated description for catalog objects.
    
    Args:
        obj: Category, ProductType, or Product instance
        language_code: Language code (e.g., 'en', 'fr', 'ar')
    
    Returns:
        Translated description or fallback to default language
    """
    if not language_code:
        language_code = settings.LANGUAGE_CODE
    
    obj_type = type(obj).__name__
    
    if obj_type not in ['Category', 'ProductType', 'Product']:
        return getattr(obj, 'description', '')
    
    translation_model = obj.translations
    
    try:
        translation = translation_model.get(language_code=language_code)
        return translation.description
    except:
        # Fall back to default language
        if language_code != settings.LANGUAGE_CODE:
            try:
                translation = translation_model.get(language_code=settings.LANGUAGE_CODE)
                return translation.description
            except:
                pass
        # Fall back to original description field
        return getattr(obj, 'description', '')


def create_default_translations(obj, language_code=None):
    """
    Create default translation entry for an object in the current language.
    Useful for when an object is first created.
    
    Args:
        obj: Catalog object instance
        language_code: Language code to create translation for
    """
    if not language_code:
        language_code = settings.LANGUAGE_CODE
    
    obj_type = type(obj).__name__
    
    if obj_type == 'Category':
        from .models import CategoryTranslation
        CategoryTranslation.objects.get_or_create(
            category=obj,
            language_code=language_code,
            defaults={'name': obj.name, 'description': obj.description}
        )
    elif obj_type == 'ProductType':
        from .models import ProductTypeTranslation
        ProductTypeTranslation.objects.get_or_create(
            product_type=obj,
            language_code=language_code,
            defaults={'name': obj.name, 'description': obj.description}
        )
    elif obj_type == 'Attribute':
        from .models import AttributeTranslation
        AttributeTranslation.objects.get_or_create(
            attribute=obj,
            language_code=language_code,
            defaults={'name': obj.name}
        )
    elif obj_type == 'AttributeOption':
        from .models import AttributeOptionTranslation
        AttributeOptionTranslation.objects.get_or_create(
            option=obj,
            language_code=language_code,
            defaults={'value': obj.value}
        )
    elif obj_type == 'Product':
        from .models import ProductTranslation
        ProductTranslation.objects.get_or_create(
            product=obj,
            language_code=language_code,
            defaults={'name': obj.name, 'description': obj.description}
        )
