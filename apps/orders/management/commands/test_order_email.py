"""
Commande Django pour tester l'envoi d'email de confirmation de commande.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.catalog.models import Product
from apps.accounts.models import SellerProfile
from apps.orders.models import Order, OrderItem
from apps.orders.services.email_service import send_order_confirmation_email
from tests.fixtures import create_seller, create_product

User = get_user_model()


class Command(BaseCommand):
    help = 'Test l\'envoi d\'email de confirmation de commande'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('TEST D\'ENVOI D\'EMAIL DE CONFIRMATION')
        self.stdout.write('='*60 + '\n')

        # Récupérer ou créer un utilisateur test avec l'email réel
        user, created = User.objects.get_or_create(
            email='saifoulayediallo2022@gmail.com',
            defaults={
                'username': 'saifoulaye',
                'first_name': 'Saifoulaye',
                'last_name': 'Diallo',
                'role': 'customer'
            }
        )

        if created:
            user.set_password('testpassword')
            user.save()
            self.stdout.write(self.style.SUCCESS('✓ Utilisateur test créé'))
        else:
            self.stdout.write('✓ Utilisateur test trouvé')

        # Récupérer ou créer un vendeur
        import random
        random_id = random.randint(10000, 99999)
        seller_user, seller_profile = create_seller(f'seller_email_{random_id}', f'seller_email_{random_id}@example.com')
        
        # Créer un produit test avec un nom unique
        product = create_product(seller_profile, f'Produit Test Email {random_id}', '99.99', 10)

        # Créer une commande test
        order = Order.objects.create(
            user=user,
            reference=f'TEST-{Order.objects.count() + 1:06d}',
            subtotal=Decimal('99.99'),
            tax=Decimal('19.99'),
            shipping_fee=Decimal('5.00'),
            discount=Decimal('10.00'),
            total_amount=Decimal('114.98'),
            currency='EUR',
            shipping_address={
                'full_name': 'Test User',
                'phone': '+33 6 12 34 56 78',
                'address1': '123 Rue de Test',
                'address2': 'Appartement 4B',
                'city': 'Paris',
                'postal_code': '75001',
                'country': 'France'
            },
            status='pending',
            payment_status='unpaid',
            customer_note='Livraison entre 9h et 12h svp'
        )

        # Créer un item de commande
        OrderItem.objects.create(
            order=order,
            seller=seller_profile,
            product=product,
            title_snapshot=product.name,
            price_snapshot=product.price,
            quantity=1,
            line_total=product.price
        )

        self.stdout.write(self.style.SUCCESS(f'✓ Commande créée: {order.reference}'))
        self.stdout.write(f'  Client: {user.get_full_name()} ({user.email})')
        self.stdout.write(f'  Montant: {order.total_amount} {order.currency}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('EMAIL (affiché dans la console):')
        self.stdout.write('='*60 + '\n')

        # Envoyer l'email
        result = send_order_confirmation_email(order)

        self.stdout.write('\n' + '='*60)
        if result:
            self.stdout.write(self.style.SUCCESS('✓ Email envoyé avec succès!'))
        else:
            self.stdout.write(self.style.ERROR('✗ Erreur lors de l\'envoi'))
        self.stdout.write('='*60 + '\n')
