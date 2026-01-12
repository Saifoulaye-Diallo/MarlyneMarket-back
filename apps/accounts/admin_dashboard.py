"""
Custom dashboard for Unfold admin with KPIs
"""
from django.db.models import Count, Q


def get_dashboard_context():
    """Fetch KPI data for admin dashboard"""
    from apps.accounts.models import User, SellerProfile
    from apps.catalog.models import Product, Category, ProductType, Attribute
    
    # User statistics
    total_sellers = User.objects.filter(role='seller').count()
    active_sellers = SellerProfile.objects.filter(is_active=True).count()
    
    # Product statistics
    total_products = Product.objects.count()
    published_products = Product.objects.filter(status='published').count()
    draft_products = Product.objects.filter(status='draft').count()
    disabled_products = Product.objects.filter(status='disabled').count()
    
    # Low stock products (stock < 10)
    low_stock_products = Product.objects.filter(stock__lt=10).count()
    
    # Recent products
    recent_products = Product.objects.all().order_by('-created_at')[:10]
    
    # Category and type counts
    total_categories = Category.objects.count()
    total_product_types = ProductType.objects.count()
    total_attributes = Attribute.objects.count()
    
    return {
        'total_sellers': total_sellers,
        'active_sellers': active_sellers,
        'total_products': total_products,
        'published_products': published_products,
        'draft_products': draft_products,
        'disabled_products': disabled_products,
        'low_stock_products': low_stock_products,
        'recent_products': recent_products,
        'total_categories': total_categories,
        'total_product_types': total_product_types,
        'total_attributes': total_attributes,
    }
