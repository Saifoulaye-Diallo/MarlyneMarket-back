# Multi-Vendor E-Commerce Marketplace Backend

A complete, production-ready Django REST Framework backend for a multi-vendor e-commerce marketplace with dynamic product types, multi-language support, and comprehensive admin/seller portals.

## Features

- **Multi-Vendor Architecture**: Sellers manage only their own products
- **Super Admin Controls**: Full control over sellers, categories, product types, and attributes
- **Dynamic Product Types**: Flexible attribute system for different product categories
- **Multi-Language Support (i18n)**: Built-in support for English, French, Spanish, Arabic
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Super Admin and Seller roles with object-level permissions
- **Comprehensive Permissions**: Sellers cannot access other sellers' data
- **Advanced Admin Interface**: Customized Django admin with role-based filtering
- **REST API**: Full RESTful API for programmatic access
- **Database Flexibility**: SQLite (dev) or PostgreSQL (production)

## Tech Stack

- Python 3.10+
- Django 4.2
- Django REST Framework 3.14
- PostgreSQL / SQLite
- JWT (djangorestframework-simplejwt)
- Pillow (image handling)

## Project Structure

```
marketplace/
├── manage.py
├── requirements.txt
├── .env.example
├── pytest.ini
├── marketplace/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/
│   │   ├── models.py           # User, SellerProfile
│   │   ├── admin.py            # Admin customization
│   │   ├── serializers.py      # DRF serializers
│   │   ├── views.py            # API viewsets
│   │   ├── permissions.py      # Custom permissions
│   │   ├── urls.py             # URL routes
│   │   └── tests.py            # Unit tests
│   └── catalog/
│       ├── models.py           # All catalog models
│       ├── admin.py            # Admin customization
│       ├── serializers.py      # DRF serializers
│       ├── views.py            # API viewsets
│       ├── permissions.py      # Custom permissions
│       ├── urls.py             # URL routes
│       └── tests.py            # Unit tests
├── locale/                     # Translation files
└── tests/
    ├── conftest.py            # Pytest fixtures
    ├── test_accounts.py       # Account tests
    └── test_catalog.py        # Catalog tests
```

## Installation

### 1. Clone and Setup

```bash
cd marketplace
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL (recommended for production)
DATABASE_URL=postgresql://user:password@localhost:5432/marketplace_db

# Or SQLite (default for development)
# Leave DB_ENGINE and related vars empty to use SQLite

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
DEFAULT_LANGUAGE=en
AVAILABLE_LANGUAGES=en,fr,es,ar
```

### 3. Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser --username admin --email admin@marketplace.local
# Password: AdminPassword123!
```

Or create with management command:
```bash
python manage.py shell
from apps.accounts.models import User
User.objects.create_superuser('admin', 'admin@marketplace.local', 'AdminPassword123!', role='super_admin')
```

### 4. Create Sample Data (Optional)

```bash
python manage.py shell
from apps.accounts.apps import create_sample_categories
create_sample_categories()
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Visit:
- Admin: http://localhost:8000/admin/
- API: http://localhost:8000/api/

## Database Schema

### Accounts App

**User** (Custom AbstractUser)
- `id` (PK)
- `username`, `email`, `password`
- `first_name`, `last_name`
- `role` (super_admin | seller)
- `is_active`, `is_staff`, `is_superuser`
- `created_at`, `updated_at`

**SellerProfile** (OneToOne with User)
- `id` (PK)
- `user` (FK to User)
- `shop_name` (translatable)
- `shop_description` (translatable)
- `phone`, `address`, `city`, `country`
- `status` (pending | active | suspended)
- `created_at`, `updated_at`

### Catalog App

**Category**
- `id` (PK)
- `name` (translatable, unique)
- `slug` (unique)
- `description` (translatable)
- `is_active`
- `created_at`, `updated_at`

**ProductType**
- `id` (PK)
- `name` (translatable, unique)
- `description` (translatable)
- `is_active`
- `created_at`, `updated_at`

**Attribute**
- `id` (PK)
- `name` (translatable)
- `data_type` (text | number | bool | choice)
- `is_active`
- `created_at`, `updated_at`

**AttributeOption**
- `id` (PK)
- `attribute` (FK to Attribute)
- `value` (translatable)
- `created_at`

**TypeAttributeRule**
- `id` (PK)
- `product_type` (FK)
- `attribute` (FK)
- `is_required` (bool)
- `display_order` (int)
- `created_at`
- Unique: (product_type, attribute)

**Product**
- `id` (PK)
- `seller` (FK to SellerProfile)
- `category` (FK to Category)
- `product_type` (FK to ProductType)
- `name` (translatable)
- `description` (translatable)
- `price` (decimal, > 0)
- `stock` (int, >= 0)
- `status` (draft | published | disabled)
- `created_at`, `updated_at`

**ProductImage**
- `id` (PK)
- `product` (FK)
- `image` (ImageField)
- `is_primary` (bool)
- `created_at`

**ProductAttributeValue**
- `id` (PK)
- `product` (FK)
- `attribute` (FK)
- `value_text`, `value_number`, `value_bool`
- `value_option` (FK to AttributeOption)
- `created_at`, `updated_at`
- Unique: (product, attribute)

## API Endpoints

### Authentication

```
POST   /api/auth/token/           # Get access token
POST   /api/auth/token/refresh/   # Refresh access token
GET    /api/auth/me/              # Get current user
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"seller@test.com","password":"testpass123"}'

# Response:
# {
#   "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "user": {
#     "id": 1,
#     "email": "seller@test.com",
#     "role": "seller",
#     ...
#   }
# }
```

### Admin Endpoints (Super Admin Only)

```
# Sellers
GET    /api/catalog/admin/sellers/
POST   /api/catalog/admin/sellers/
GET    /api/catalog/admin/sellers/{id}/
PATCH  /api/catalog/admin/sellers/{id}/
POST   /api/catalog/admin/sellers/{id}/activate/
POST   /api/catalog/admin/sellers/{id}/suspend/
GET    /api/catalog/admin/sellers/pending/

# Categories
GET    /api/catalog/admin/categories/
POST   /api/catalog/admin/categories/
GET    /api/catalog/admin/categories/{id}/
PUT    /api/catalog/admin/categories/{id}/
PATCH  /api/catalog/admin/categories/{id}/
DELETE /api/catalog/admin/categories/{id}/

# Product Types
GET    /api/catalog/admin/product-types/
POST   /api/catalog/admin/product-types/
GET    /api/catalog/admin/product-types/{id}/
PUT    /api/catalog/admin/product-types/{id}/
PATCH  /api/catalog/admin/product-types/{id}/
DELETE /api/catalog/admin/product-types/{id}/

# Attributes
GET    /api/catalog/admin/attributes/
POST   /api/catalog/admin/attributes/
GET    /api/catalog/admin/attributes/{id}/
PUT    /api/catalog/admin/attributes/{id}/
PATCH  /api/catalog/admin/attributes/{id}/
DELETE /api/catalog/admin/attributes/{id}/

# Attribute Options
GET    /api/catalog/admin/attribute-options/
POST   /api/catalog/admin/attribute-options/

# Type Attribute Rules
GET    /api/catalog/admin/type-attribute-rules/
POST   /api/catalog/admin/type-attribute-rules/
DELETE /api/catalog/admin/type-attribute-rules/{id}/

# Product Type Schema (read-only, accessible to all)
GET    /api/catalog/admin/product-types/{id}/schema/
```

### Seller Endpoints (Seller Only)

```
# Products (own only)
GET    /api/catalog/seller/products/
POST   /api/catalog/seller/products/
GET    /api/catalog/seller/products/{id}/
PATCH  /api/catalog/seller/products/{id}/
DELETE /api/catalog/seller/products/{id}/
POST   /api/catalog/seller/products/{id}/publish/
POST   /api/catalog/seller/products/{id}/draft/
POST   /api/catalog/seller/products/{id}/disable/

# Product Images (own products only)
GET    /api/catalog/seller/products/{product_pk}/images/
POST   /api/catalog/seller/products/{product_pk}/images/
GET    /api/catalog/seller/products/{product_pk}/images/{id}/
PATCH  /api/catalog/seller/products/{product_pk}/images/{id}/
DELETE /api/catalog/seller/products/{product_pk}/images/{id}/

# Product Attributes (own products only)
GET    /api/catalog/seller/products/{product_pk}/attributes/
POST   /api/catalog/seller/products/{product_pk}/attributes/
PATCH  /api/catalog/seller/products/{product_pk}/attributes/{id}/
DELETE /api/catalog/seller/products/{product_pk}/attributes/{id}/
```

## Example API Calls

### 1. Create a Product

```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"seller@test.com","password":"testpass"}' | jq -r '.access')

# Create product
curl -X POST http://localhost:8000/api/catalog/seller/products/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": 1,
    "product_type": 1,
    "name": "Gaming Laptop",
    "description": "High-performance gaming laptop",
    "price": "1999.99",
    "stock": 5,
    "status": "draft"
  }'
```

### 2. Add Product Attributes

```bash
curl -X POST http://localhost:8000/api/catalog/seller/products/1/attributes/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "attribute": 1,
    "value_text": "ASUS"
  }'
```

### 3. Publish Product

```bash
curl -X POST http://localhost:8000/api/catalog/seller/products/1/publish/ \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Upload Product Image

```bash
curl -X POST http://localhost:8000/api/catalog/seller/products/1/images/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/image.jpg" \
  -F "is_primary=true"
```

## Permissions & Security

### Role-Based Access Control

**Super Admin:**
- Full CRUD on all resources (sellers, categories, product types, attributes)
- Can view all products from all sellers
- Can manage seller status (activate, suspend)

**Seller:**
- View only their own products
- Create and manage only their own products
- Cannot create/edit categories, product types, or attributes
- Cannot access other sellers' data
- Cannot change product seller assignment

### Object-Level Permissions

All seller resources are protected by `IsOwnProduct` permission:
```python
# Only works for products belonging to the authenticated seller
GET /api/catalog/seller/products/{id}/ -> Returns 404 if not owned
```

### Data Isolation

- `Product.seller` is automatically set from `request.user.seller_profile`
- Never trust client-provided seller IDs
- Always filter querysets by authenticated user

## Business Rules & Validation

### Product Publication

A product **cannot be published** unless:
1. All **required attributes** (marked `is_required=True`) have values
2. Price > 0
3. Stock >= 0
4. At least one image (optional but recommended)

```python
# Example: Product with required Brand and RAM attributes
if product.can_be_published():
    product.status = 'published'
    product.save()
else:
    # Missing required attributes
    error: "Required attributes missing"
```

### Attribute Validation

- Attribute values must match their `data_type`:
  - `text` → `value_text`
  - `number` → `value_number`
  - `bool` → `value_bool`
  - `choice` → `value_option` (must exist in AttributeOption)

### Product Type Rules

- Super admin defines which attributes are required/optional per product type
- Sellers **cannot** create custom attributes
- Sellers can only use existing product types and their defined attributes

## Multi-Language Support (i18n)

### Translatable Fields

All user-facing text is translatable:
- `Category.name`
- `ProductType.name`
- `Attribute.name`
- `AttributeOption.value`
- `Product.name`
- `Product.description`

### Language Configuration

In `.env`:
```
DEFAULT_LANGUAGE=en
AVAILABLE_LANGUAGES=en,fr,es,ar
```

In Django admin:
- Users can select language preference (top right)
- All translatable fields will display in that language

### API Language Support

Send `Accept-Language` header:
```bash
curl -H "Accept-Language: fr" http://localhost:8000/api/catalog/admin/categories/
# Returns French translations
```

### Adding New Languages

1. Edit `.env`:
   ```
   AVAILABLE_LANGUAGES=en,fr,es,ar,de
   ```

2. Create translation files:
   ```bash
   python manage.py makemessages -l de
   python manage.py compilemessages
   ```

3. Translate in `locale/de/LC_MESSAGES/django.po`

4. Recompile:
   ```bash
   python manage.py compilemessages
   ```

## Testing

### Run Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_accounts.py

# Specific test
pytest tests/test_catalog.py::TestProductPermissions::test_seller_cannot_access_other_seller_product

# With coverage
pytest --cov=apps tests/
```

### Test Coverage

- ✓ Seller cannot access other seller's product
- ✓ Seller can access own product
- ✓ Seller can only list own products
- ✓ Cannot publish without required attributes
- ✓ Can publish with all required attributes
- ✓ Price validation (> 0)
- ✓ Stock validation (>= 0)
- ✓ Admin-only permissions

### Sample Fixtures

See `tests/conftest.py`:
- `super_admin`: Superuser with admin role
- `seller_user`: Regular seller with profile
- `seller_user_2`: Another seller for permission tests
- `product_type`: Laptop type with attributes
- `attribute_text`, `attribute_number`, `attribute_choice`
- `type_attribute_rules`: Rules linking product type and attributes
- `product`: Draft product
- `published_product`: Published product with all attributes

## Django Admin Interface

### Super Admin Dashboard

Access: http://localhost:8000/admin/

**Available Options:**
- Users: Create/edit/deactivate users
- Seller Profiles: Manage sellers, activate/suspend
- Categories: Full CRUD on product categories
- Product Types: Create/manage product types
- Attributes: Create/manage attributes with data types
- Attribute Options: Add options to choice attributes
- Type Attribute Rules: Define required attributes per product type
- Products: View all products, see publication status
- Product Images: Manage product images
- Product Attribute Values: View/edit attribute values

### Seller Dashboard

When logged in as seller:
- Products: Only see own products
- Product Images: Only manage images for own products
- Product Attribute Values: Only manage attributes for own products
- **Cannot access:** Categories, Product Types, Attributes

## Performance Considerations

### Database Optimization

- **Indexes**: Added on frequently queried fields:
  - `Product.seller`, `Product.status`
  - `Product.category`, `Product.product_type`
  - `ProductAttributeValue.product`, `ProductAttributeValue.attribute`

- **Query Optimization**:
  - Use `select_related()` for ForeignKeys
  - Use `prefetch_related()` for reverse relations
  - Implement pagination (20 items per page by default)

### Caching (Optional Future Enhancement)

```python
# Example: Cache product type schema
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # 5 minutes
def product_type_schema(request, pk):
    ...
```

## Deployment

### Environment Setup

```bash
# Production
SECRET_KEY=<generate-secure-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@prod-db:5432/marketplace
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

### Create Superuser

```bash
python manage.py createsuperuser
```

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Run Migrations

```bash
python manage.py migrate
```

### WSGI Server (Gunicorn)

```bash
pip install gunicorn
gunicorn marketplace.wsgi --bind 0.0.0.0:8000 --workers 4
```

## Future Enhancements (V2)

- [ ] Order management system
- [ ] Payment gateway integration (Stripe, PayPal)
- [ ] Commission calculation for sellers
- [ ] Inventory management (low stock alerts)
- [ ] Product reviews and ratings
- [ ] Seller messaging system
- [ ] Advanced analytics and reporting
- [ ] Mobile app API endpoints
- [ ] Webhooks for order updates
- [ ] Multi-currency support

## Security Checklist

- ✓ JWT token-based authentication
- ✓ Object-level permissions (sellers can't access others' data)
- ✓ CSRF protection (Django middleware)
- ✓ SQL injection prevention (ORM)
- ✓ Rate limiting (can be added with throttling)
- ✓ Input validation (serializers)
- ✓ Environment variable configuration (no hardcoded secrets)
- ✓ Password hashing (Django User model)
- ⚠ Consider adding: 2FA, API key management, audit logging

## Troubleshooting

### Database Errors

```bash
# Reset database (development only!)
python manage.py flush
python manage.py migrate
python manage.py createsuperuser

# Check migrations
python manage.py showmigrations
```

### Permission Denied (403)

- Check JWT token is valid and not expired
- Verify user role (super_admin vs seller)
- Ensure object belongs to authenticated user

### "Module not found" Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Update Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Static Files Not Loading

```bash
python manage.py collectstatic
python manage.py findstatic admin/css/base.css
```

## Support & Documentation

- Django: https://docs.djangoproject.com/
- DRF: https://www.django-rest-framework.org/
- JWT: https://django-rest-framework-simplejwt.readthedocs.io/
- i18n: https://docs.djangoproject.com/en/stable/topics/i18n/

## License

MIT License - Feel free to use in your projects!

## Contributing

1. Create feature branch
2. Write tests
3. Run pytest
4. Submit PR

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-10  
**Django**: 4.2+  
**Python**: 3.10+
