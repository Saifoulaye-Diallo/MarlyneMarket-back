# 🧪 Guide de Test Cloudinary

## 1. Vérification de la Configuration

### Test des credentials
```bash
cd "C:/Users/Saifon/Desktop/PROJET BOUTIQUE/marketplace"
python test_cloudinary.py
```

### Vérification des settings Django
```bash
python manage.py shell -c "
from django.conf import settings
print('INSTALLED_APPS avec Cloudinary:')
for app in settings.INSTALLED_APPS:
    if 'cloud' in app:
        print(f'  - {app}')

if hasattr(settings, 'CLOUDINARY_STORAGE'):
    print(f'CLOUDINARY_STORAGE configuré: {bool(settings.CLOUDINARY_STORAGE)}')
"
```

## 2. Test via l'API Django

### Créer un utilisateur vendeur
```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.accounts.models import SellerProfile

User = get_user_model()
user, created = User.objects.get_or_create(
    email='seller@test.com',
    defaults={
        'first_name': 'Test',
        'last_name': 'Seller', 
        'role': 'seller'
    }
)
user.set_password('testpass123')
user.save()

seller, created = SellerProfile.objects.get_or_create(
    user=user,
    defaults={
        'shop_name': 'Test Shop',
        'approval_status': 'approved'
    }
)

print(f'User créé: {user.email}')
print(f'Seller créé: {seller.shop_name}')
"
```

### Créer un produit de test
```bash
python manage.py shell -c "
from apps.catalog.models import Category, ProductType, Product
from apps.accounts.models import SellerProfile

seller = SellerProfile.objects.first()
category, _ = Category.objects.get_or_create(name='Test Category')
product_type, _ = ProductType.objects.get_or_create(name='Test Type')

product, created = Product.objects.get_or_create(
    name='Test Product',
    defaults={
        'description': 'Test Description',
        'category': category,
        'product_type': product_type,
        'seller': seller,
        'price': 100.00,
        'status': 'published'
    }
)

print(f'Product créé: {product.name} (ID: {product.id})')
"
```

## 3. Test avec cURL

### Obtenir un token
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "seller@test.com", "password": "testpass123"}'
```

### Upload d'image (remplacez TOKEN et PRODUCT_ID)
```bash
curl -X POST http://127.0.0.1:8000/api/catalog/seller/products/PRODUCT_ID/images/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@path/to/your/image.jpg" \
  -F "alt_text=Test image" \
  -F "is_primary=true"
```

## 4. Test Postman

1. **Importer votre collection** Marketplace_API_Complete_Clean.postman_collection.json
2. **Définir les variables** :
   - `base_url`: http://127.0.0.1:8000
   - `seller_email`: seller@test.com  
   - `seller_password`: testpass123

3. **Exécuter dans l'ordre** :
   - Login Seller
   - Create Product (noter l'ID)
   - Upload Product Image

## 5. Vérifications

### Vérifier les images uploadées
```bash
python manage.py shell -c "
from apps.catalog.models import ProductImage
images = ProductImage.objects.all()
for img in images:
    print(f'Image: {img.id} - {img.alt_text}')
    print(f'URL: {img.image.url if img.image else \"Pas d'URL\"}')
"
```

### Nettoyer les tests
```bash
python manage.py shell -c "
from apps.catalog.models import ProductImage, Product
from apps.accounts.models import SellerProfile, User

# Supprimer les images de test
ProductImage.objects.filter(alt_text__icontains='test').delete()

# Supprimer les produits de test  
Product.objects.filter(name__icontains='test').delete()

print('Données de test nettoyées')
"
```

## ⚠️ Problèmes Courants

1. **Invalid API Key** : Vérifiez vos credentials Cloudinary
2. **403 Forbidden** : Vérifiez que l'utilisateur est bien un seller approuvé
3. **404 Product** : Vérifiez que le produit appartient au seller connecté
4. **File too large** : Max 5MB par défaut
5. **Invalid format** : Seuls JPG, PNG, WEBP autorisés