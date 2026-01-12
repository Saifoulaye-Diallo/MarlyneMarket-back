#!/usr/bin/env python
"""
Script pour générer des données fictives pour la marketplace africaine.
Ce script crée des utilisateurs, vendeurs, produits, commandes et reviews réalistes.
"""
import os
import sys
import django
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta
import random
from faker import Faker

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'african_back_end.settings.dev')
django.setup()

# Imports des modèles après la configuration Django
from django.contrib.auth import get_user_model
from apps.accounts.models import SellerProfile
from apps.customers.models import CustomerProfile, Address
from apps.catalog.models import (
    Category, ProductType, Attribute, AttributeOption, 
    Product, ProductImage, ProductAttributeValue, TypeAttributeRule
)
from apps.orders.models import Order, OrderItem, SellerOrder
from apps.payments.models import Payment
from apps.reviews.models import Review
from apps.promotions.models import Coupon, CouponUsage
from apps.returns.models import ReturnRequest

User = get_user_model()

# Configuration Faker en français
fake = Faker('fr_FR')

# Données spécifiques au contexte africain
AFRICAN_CITIES = [
    'Dakar', 'Lagos', 'Abidjan', 'Accra', 'Casablanca', 'Tunis',
    'Nairobi', 'Addis Ababa', 'Kinshasa', 'Douala', 'Yaoundé',
    'Bamako', 'Ouagadougou', 'Lomé', 'Cotonou', 'Conakry'
]

AFRICAN_COUNTRIES = [
    'Sénégal', 'Nigeria', 'Côte d\'Ivoire', 'Ghana', 'Maroc', 'Tunisie',
    'Kenya', 'Éthiopie', 'République Démocratique du Congo', 'Cameroun',
    'Mali', 'Burkina Faso', 'Togo', 'Bénin', 'Guinée'
]

PRODUCT_CATEGORIES = [
    ('Artisanat Traditionnel', 'Objets artisanaux authentiques d\'Afrique'),
    ('Vêtements & Mode', 'Vêtements traditionnels et modernes'),
    ('Bijoux & Accessoires', 'Bijoux traditionnels et contemporains'),
    ('Cosmétiques Naturels', 'Produits de beauté à base d\'ingrédients africains'),
    ('Épices & Condiments', 'Épices et condiments africains authentiques'),
    ('Textiles & Tissus', 'Tissus traditionnels comme le wax, le bogolan'),
    ('Instruments de Musique', 'Instruments traditionnels africains'),
    ('Décoration Intérieure', 'Objets décoratifs et meubles africains'),
    ('Alimentation Bio', 'Produits alimentaires biologiques d\'Afrique'),
    ('Livres & Culture', 'Livres et objets culturels africains')
]

AFRICAN_NAMES = [
    'Aminata', 'Fatou', 'Aïssatou', 'Marième', 'Khady', 'Coumba',
    'Moussa', 'Amadou', 'Ousmane', 'Ibrahima', 'Mamadou', 'Seydou',
    'Adama', 'Salif', 'Bakary', 'Awa', 'Ndeye', 'Aby', 'Kone', 'Traore'
]

def clear_existing_data():
    """Supprime toutes les données existantes."""
    print("🗑️  Suppression des données existantes...")
    
    # Supprimer dans l'ordre des dépendances
    ReturnRequest.objects.all().delete()
    CouponUsage.objects.all().delete()
    Coupon.objects.all().delete()
    Review.objects.all().delete()
    Payment.objects.all().delete()
    OrderItem.objects.all().delete()
    SellerOrder.objects.all().delete()
    Order.objects.all().delete()
    
    ProductAttributeValue.objects.all().delete()
    ProductImage.objects.all().delete()
    Product.objects.all().delete()
    TypeAttributeRule.objects.all().delete()
    AttributeOption.objects.all().delete()
    Attribute.objects.all().delete()
    ProductType.objects.all().delete()
    Category.objects.all().delete()
    
    Address.objects.all().delete()
    CustomerProfile.objects.all().delete()
    SellerProfile.objects.all().delete()
    
    # Supprimer tous les utilisateurs sauf les superusers
    User.objects.filter(is_superuser=False).delete()
    
    print("✅ Données supprimées avec succès!")

def create_categories():
    """Crée les catégories de produits."""
    print("📂 Création des catégories...")
    categories = []
    
    for name, description in PRODUCT_CATEGORIES:
        slug = name.lower().replace(' ', '-').replace('&', 'et').replace('\'', '')
        category = Category.objects.create(
            name=name,
            slug=slug,
            description=description,
            is_active=True
        )
        categories.append(category)
    
    print(f"✅ {len(categories)} catégories créées!")
    return categories

def create_product_types():
    """Crée les types de produits."""
    print("🏷️  Création des types de produits...")
    product_types = []
    
    type_definitions = [
        ('Vêtement', 'Articles vestimentaires'),
        ('Bijou', 'Bijoux et accessoires'),
        ('Artisanat', 'Objets artisanaux'),
        ('Cosmétique', 'Produits de beauté'),
        ('Épice', 'Épices et condiments'),
        ('Textile', 'Tissus et textiles'),
        ('Instrument', 'Instruments de musique'),
        ('Décoration', 'Objets décoratifs'),
        ('Aliment', 'Produits alimentaires'),
        ('Livre', 'Livres et supports culturels')
    ]
    
    for name, description in type_definitions:
        product_type = ProductType.objects.create(
            name=name,
            description=description,
            is_active=True
        )
        product_types.append(product_type)
    
    print(f"✅ {len(product_types)} types de produits créés!")
    return product_types

def create_attributes():
    """Crée les attributs produits."""
    print("🏗️  Création des attributs...")
    attributes = []
    
    # Attributs communs
    common_attributes = [
        ('Couleur', 'choice'),
        ('Taille', 'choice'),
        ('Matériau', 'choice'),
        ('Poids', 'number'),
        ('Origine', 'choice'),
        ('Artisan', 'text'),
        ('Certification Bio', 'bool'),
        ('Fait Main', 'bool')
    ]
    
    for name, data_type in common_attributes:
        attribute = Attribute.objects.create(
            name=name,
            data_type=data_type,
            is_active=True
        )
        attributes.append(attribute)
        
        # Ajouter des options pour les attributs de type choice
        if data_type == 'choice':
            if name == 'Couleur':
                colors = ['Rouge', 'Bleu', 'Vert', 'Jaune', 'Blanc', 'Noir', 
                         'Orange', 'Violet', 'Marron', 'Beige', 'Rose']
                for color in colors:
                    AttributeOption.objects.create(
                        attribute=attribute,
                        value=color,
                        display_order=colors.index(color)
                    )
            elif name == 'Taille':
                sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'Unique']
                for size in sizes:
                    AttributeOption.objects.create(
                        attribute=attribute,
                        value=size,
                        display_order=sizes.index(size)
                    )
            elif name == 'Matériau':
                materials = ['Coton', 'Soie', 'Lin', 'Cuir', 'Bois', 'Métal', 
                           'Pierre', 'Céramique', 'Verre', 'Plastique recyclé']
                for material in materials:
                    AttributeOption.objects.create(
                        attribute=attribute,
                        value=material,
                        display_order=materials.index(material)
                    )
            elif name == 'Origine':
                for country in AFRICAN_COUNTRIES:
                    AttributeOption.objects.create(
                        attribute=attribute,
                        value=country,
                        display_order=AFRICAN_COUNTRIES.index(country)
                    )
    
    print(f"✅ {len(attributes)} attributs créés avec leurs options!")
    return attributes

def create_users_and_profiles():
    """Crée des utilisateurs avec profils vendeurs et clients."""
    print("👥 Création des utilisateurs et profils...")
    
    users_data = []
    
    # Créer des vendeurs
    print("  👨‍💼 Création des vendeurs...")
    for i in range(15):  # 15 vendeurs
        first_name = random.choice(AFRICAN_NAMES)
        last_name = fake.last_name()
        username = f"seller_{first_name.lower()}_{i+1}"
        email = f"{username}@marketplace-afrique.com"
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password='seller123',
            first_name=first_name,
            last_name=last_name,
            role='seller',
            phone_number=fake.phone_number(),
            birth_date=fake.date_of_birth(minimum_age=25, maximum_age=65),
            account_status='active',
            is_email_verified=True,
            is_phone_verified=True
        )
        
        # Créer le profil vendeur
        seller_profile = SellerProfile.objects.create(
            user=user,
            business_name=f"Boutique {first_name}",
            business_type=random.choice(['individual', 'company']),
            tax_id=f"TAX{random.randint(100000, 999999)}",
            business_address={
                'address': fake.address(),
                'city': random.choice(AFRICAN_CITIES),
                'country': random.choice(AFRICAN_COUNTRIES)
            },
            business_phone=fake.phone_number(),
            business_email=f"business_{username}@marketplace-afrique.com",
            bio=f"Artisan passionné spécialisé dans l'art traditionnel de {random.choice(AFRICAN_COUNTRIES)}.",
            verification_status='verified',
            commission_rate=Decimal('10.00'),
            is_active=True,
            featured=random.choice([True, False])
        )
        
        users_data.append({'user': user, 'seller_profile': seller_profile})
    
    # Créer des clients
    print("  🛍️  Création des clients...")
    for i in range(50):  # 50 clients
        first_name = random.choice(AFRICAN_NAMES)
        last_name = fake.last_name()
        username = f"customer_{first_name.lower()}_{i+1}"
        email = f"{username}@email.com"
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password='customer123',
            first_name=first_name,
            last_name=last_name,
            role='customer',
            phone_number=fake.phone_number(),
            birth_date=fake.date_of_birth(minimum_age=18, maximum_age=70),
            account_status='active',
            is_email_verified=True,
            is_phone_verified=random.choice([True, False])
        )
        
        # Créer le profil client
        customer_profile = CustomerProfile.objects.create(
            user=user,
            phone=fake.phone_number()
        )
        
        # Créer 1-3 adresses par client
        for j in range(random.randint(1, 3)):
            Address.objects.create(
                user=user,
                label=random.choice(['Domicile', 'Bureau', 'Parents']),
                full_name=f"{user.first_name} {user.last_name}",
                phone=fake.phone_number(),
                address1=fake.street_address(),
                address2=fake.secondary_address() if random.choice([True, False]) else '',
                city=random.choice(AFRICAN_CITIES),
                region=fake.state(),
                postal_code=fake.postcode(),
                country=random.choice(AFRICAN_COUNTRIES),
                is_default_shipping=j == 0,  # Première adresse = défaut
                is_default_billing=j == 0
            )
        
        users_data.append({'user': user, 'customer_profile': customer_profile})
    
    print(f"✅ {len(users_data)} utilisateurs créés!")
    return users_data

def create_products(categories, product_types, attributes, sellers):
    """Crée les produits avec leurs attributs."""
    print("🛍️  Création des produits...")
    products = []
    
    # Produits exemples authentiques africains
    product_examples = [
        {
            'name': 'Boubou Traditionnel Brodé',
            'description': 'Magnifique boubou traditionnel avec broderies dorées à la main.',
            'category': 'Vêtements & Mode',
            'type': 'Vêtement',
            'base_price': Decimal('89.99')
        },
        {
            'name': 'Collier en Perles de Baobab',
            'description': 'Collier artisanal fait avec des graines de baobab et perles traditionnelles.',
            'category': 'Bijoux & Accessoires',
            'type': 'Bijou',
            'base_price': Decimal('34.50')
        },
        {
            'name': 'Masque Dogon Authentique',
            'description': 'Masque traditionnel Dogon sculpté dans du bois d\'iroko.',
            'category': 'Artisanat Traditionnel',
            'type': 'Artisanat',
            'base_price': Decimal('156.00')
        },
        {
            'name': 'Beurre de Karité Bio',
            'description': 'Beurre de karité 100% pur et biologique du Burkina Faso.',
            'category': 'Cosmétiques Naturels',
            'type': 'Cosmétique',
            'base_price': Decimal('24.99')
        },
        {
            'name': 'Piment Rouge de Cayenne',
            'description': 'Piment rouge séché cultivé traditionnellement en Côte d\'Ivoire.',
            'category': 'Épices & Condiments',
            'type': 'Épice',
            'base_price': Decimal('12.50')
        },
        {
            'name': 'Tissu Wax Authentique',
            'description': 'Tissu wax traditionnel aux motifs géométriques colorés.',
            'category': 'Textiles & Tissus',
            'type': 'Textile',
            'base_price': Decimal('45.00')
        },
        {
            'name': 'Djembé Professionnel',
            'description': 'Djembé artisanal avec peau de chèvre et sculpture traditionnelle.',
            'category': 'Instruments de Musique',
            'type': 'Instrument',
            'base_price': Decimal('120.00')
        },
        {
            'name': 'Sculpture Éléphant en Ébène',
            'description': 'Sculpture d\'éléphant minutieusement taillée dans l\'ébène.',
            'category': 'Décoration Intérieure',
            'type': 'Décoration',
            'base_price': Decimal('78.00')
        }
    ]
    
    # Créer les produits basés sur les exemples
    for example in product_examples:
        # Créer plusieurs variations de chaque exemple
        for i in range(random.randint(2, 5)):
            category = next(c for c in categories if c.name == example['category'])
            product_type = next(pt for pt in product_types if pt.name == example['type'])
            seller = random.choice(sellers)['seller_profile']
            
            # Variation du nom
            variant_name = example['name']
            if i > 0:
                variants = [' Premium', ' Artisanal', ' Traditionnel', ' Moderne', ' Collector']
                variant_name += random.choice(variants)
            
            # Variation du prix
            price_variation = Decimal(str(random.uniform(0.8, 1.5)))
            final_price = example['base_price'] * price_variation
            
            product = Product.objects.create(
                seller=seller,
                category=category,
                product_type=product_type,
                title=variant_name,
                description=example['description'],
                price=final_price,
                stock_quantity=random.randint(5, 50),
                weight=Decimal(str(random.uniform(0.1, 5.0))),
                sku=f"PROD-{random.randint(100000, 999999)}",
                status='active' if random.random() > 0.1 else 'draft',
                is_featured=random.choice([True, False]),
                meta_title=variant_name,
                meta_description=example['description'][:160]
            )
            
            products.append(product)
            
            # Ajouter des valeurs d'attributs
            relevant_attributes = attributes[:random.randint(3, 6)]
            for attribute in relevant_attributes:
                if attribute.data_type == 'choice' and attribute.options.exists():
                    option = random.choice(list(attribute.options.all()))
                    ProductAttributeValue.objects.create(
                        product=product,
                        attribute=attribute,
                        value_option=option
                    )
                elif attribute.data_type == 'text':
                    text_values = {
                        'Artisan': fake.name(),
                        'Description': fake.sentence()
                    }
                    value = text_values.get(attribute.name, fake.word())
                    ProductAttributeValue.objects.create(
                        product=product,
                        attribute=attribute,
                        value_text=value
                    )
                elif attribute.data_type == 'number':
                    if attribute.name == 'Poids':
                        value = Decimal(str(random.uniform(0.1, 10.0)))
                    else:
                        value = Decimal(str(random.randint(1, 100)))
                    ProductAttributeValue.objects.create(
                        product=product,
                        attribute=attribute,
                        value_number=value
                    )
                elif attribute.data_type == 'bool':
                    ProductAttributeValue.objects.create(
                        product=product,
                        attribute=attribute,
                        value_bool=random.choice([True, False])
                    )
    
    print(f"✅ {len(products)} produits créés!")
    return products

def create_coupons():
    """Crée des coupons de réduction."""
    print("🎫 Création des coupons...")
    coupons = []
    
    coupon_data = [
        ('WELCOME10', 'percentage', 10, 'Bienvenue - 10% de réduction'),
        ('AFRICA20', 'percentage', 20, 'Promotion Afrique - 20% de réduction'),
        ('SUMMER15', 'percentage', 15, 'Promo été - 15% de réduction'),
        ('ARTISAN5', 'fixed', 5, 'Réduction artisan - 5€ de réduction'),
        ('NEWCLIENT', 'percentage', 25, 'Nouveau client - 25% de réduction'),
    ]
    
    for code, discount_type, value, description in coupon_data:
        coupon = Coupon.objects.create(
            code=code,
            description=description,
            discount_type=discount_type,
            discount_value=Decimal(str(value)),
            usage_limit=random.randint(50, 200),
            minimum_order_amount=Decimal('20.00') if discount_type == 'percentage' else Decimal('10.00'),
            valid_from=datetime.now() - timedelta(days=30),
            valid_until=datetime.now() + timedelta(days=60),
            is_active=True
        )
        coupons.append(coupon)
    
    print(f"✅ {len(coupons)} coupons créés!")
    return coupons

def create_orders(customers, products, coupons):
    """Crée des commandes avec articles."""
    print("🛒 Création des commandes...")
    orders = []
    
    for i in range(100):  # 100 commandes
        customer = random.choice([u for u in customers if u['user'].role == 'customer'])
        customer_user = customer['user']
        
        # Adresse de livraison
        customer_address = customer_user.addresses.first()
        shipping_address = {
            'full_name': f"{customer_user.first_name} {customer_user.last_name}",
            'address1': customer_address.address1 if customer_address else fake.street_address(),
            'city': customer_address.city if customer_address else random.choice(AFRICAN_CITIES),
            'country': customer_address.country if customer_address else random.choice(AFRICAN_COUNTRIES),
            'postal_code': customer_address.postal_code if customer_address else fake.postcode(),
            'phone': customer_address.phone if customer_address else fake.phone_number()
        }
        
        order = Order.objects.create(
            user=customer_user,
            reference=f"ORD-{random.randint(100000, 999999)}",
            status=random.choice(['pending', 'paid', 'processing', 'shipped', 'delivered']),
            payment_status=random.choice(['unpaid', 'paid']),
            shipping_address=shipping_address,
            customer_note=fake.sentence() if random.choice([True, False]) else '',
            currency='EUR'
        )
        
        # Ajouter des articles à la commande
        order_items = []
        num_items = random.randint(1, 5)
        order_total = Decimal('0.00')
        
        selected_products = random.sample(
            [p for p in products if p.status == 'active'],
            min(num_items, len([p for p in products if p.status == 'active']))
        )
        
        for product in selected_products:
            quantity = random.randint(1, 3)
            line_total = product.price * quantity
            order_total += line_total
            
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                title_snapshot=product.title,
                price_snapshot=product.price,
                quantity=quantity,
                line_total=line_total
            )
            order_items.append(order_item)
            
            # Créer SellerOrder pour chaque vendeur
            SellerOrder.objects.get_or_create(
                order=order,
                seller=product.seller,
                defaults={
                    'status': order.status,
                    'subtotal': line_total
                }
            )
        
        # Appliquer un coupon parfois
        if random.random() < 0.3:  # 30% de chance
            coupon = random.choice(coupons)
            order.coupon_code = coupon.code
            if coupon.discount_type == 'percentage':
                discount = order_total * (coupon.discount_value / 100)
            else:
                discount = coupon.discount_value
            order.discount = min(discount, order_total)
        
        # Calculer les totaux
        order.subtotal = order_total
        order.shipping_fee = Decimal('5.00') if order_total < 50 else Decimal('0.00')
        order.tax = order_total * Decimal('0.20')  # 20% TVA
        order.total_amount = order.subtotal + order.shipping_fee + order.tax - order.discount
        order.save()
        
        # Créer un paiement si la commande est payée
        if order.payment_status == 'paid':
            Payment.objects.create(
                order=order,
                provider='stripe',
                amount=order.total_amount,
                currency=order.currency,
                status='succeeded',
                provider_intent_id=f"pi_test_{random.randint(100000, 999999)}"
            )
        
        orders.append(order)
    
    print(f"✅ {len(orders)} commandes créées!")
    return orders

def create_reviews(customers, products):
    """Crée des avis produits."""
    print("⭐ Création des avis produits...")
    reviews = []
    
    review_templates = [
        "Excellent produit, très satisfait de mon achat !",
        "Produit conforme à la description, livraison rapide.",
        "Très belle qualité artisanale, je recommande vivement.",
        "Produit authentique et magnifique, parfait pour un cadeau.",
        "Livraison un peu longue mais le produit en vaut la peine.",
        "Superbe travail d'artisan, les détails sont magnifiques.",
        "Produit de qualité moyenne, sans plus.",
        "Très déçu, le produit ne correspond pas aux photos.",
        "Service client au top, problème résolu rapidement.",
        "Emballage soigné, produit arrivé en parfait état."
    ]
    
    for i in range(200):  # 200 avis
        customer = random.choice([u for u in customers if u['user'].role == 'customer'])
        product = random.choice(products)
        
        review = Review.objects.create(
            user=customer['user'],
            product=product,
            rating=random.randint(3, 5),  # Plutôt positif
            title=f"Avis sur {product.title}",
            comment=random.choice(review_templates),
            is_approved=True,
            is_verified_purchase=random.choice([True, False])
        )
        reviews.append(review)
    
    print(f"✅ {len(reviews)} avis créés!")
    return reviews

def main():
    """Fonction principale."""
    print("🚀 Démarrage de la génération des données fictives...")
    print("=" * 60)
    
    # Étapes de génération
    clear_existing_data()
    
    categories = create_categories()
    product_types = create_product_types()
    attributes = create_attributes()
    users_data = create_users_and_profiles()
    products = create_products(categories, product_types, attributes, users_data)
    coupons = create_coupons()
    orders = create_orders(users_data, products, coupons)
    reviews = create_reviews(users_data, products)
    
    print("=" * 60)
    print("🎉 Génération terminée avec succès !")
    print("\n📊 Résumé des données créées:")
    print(f"   👥 Utilisateurs: {User.objects.count()}")
    print(f"   🏪 Vendeurs: {SellerProfile.objects.count()}")
    print(f"   🛍️  Clients: {CustomerProfile.objects.count()}")
    print(f"   📂 Catégories: {len(categories)}")
    print(f"   🛍️  Produits: {len(products)}")
    print(f"   🛒 Commandes: {len(orders)}")
    print(f"   ⭐ Avis: {len(reviews)}")
    print(f"   🎫 Coupons: {len(coupons)}")
    print("\n🔑 Comptes de test:")
    print("   - Vendeurs: seller_[nom]_[numéro] / seller123")
    print("   - Clients: customer_[nom]_[numéro] / customer123")
    print("\n✨ Votre marketplace africaine est prête à être testée !")

if __name__ == "__main__":
    main()