from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import CustomerProfile, Address
from decimal import Decimal

User = get_user_model()


class CustomerProfileModelTest(TestCase):
    """Tests pour le modèle CustomerProfile"""
    
    def setUp(self):
        """Créer un profil client de test"""
        self.user = User.objects.create_user(
            username='customer1',
            email='customer1@example.com',
            password='pass123',
            role='customer'
        )
        self.profile = CustomerProfile.objects.create(
            user=self.user,
            phone_number='+33612345678',
            preferred_language='fr',
            preferred_currency='EUR',
            customer_tier='gold'
        )
    
    def test_profile_creation(self):
        """Test la création d'un profil client"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.preferred_language, 'fr')
        self.assertEqual(self.profile.preferred_currency, 'EUR')
    
    def test_profile_defaults(self):
        """Test les valeurs par défaut"""
        self.assertTrue(self.profile.subscribe_to_newsletter)
        self.assertTrue(self.profile.receive_promotional_emails)
        self.assertTrue(self.profile.receive_order_notifications)
        self.assertEqual(self.profile.total_orders, 0)
        self.assertEqual(self.profile.total_spent, Decimal('0'))
        self.assertEqual(self.profile.loyalty_points, 0)
    
    def test_customer_tiers(self):
        """Test les niveaux de client"""
        valid_tiers = ['bronze', 'silver', 'gold', 'platinum']
        for tier in valid_tiers:
            self.profile.customer_tier = tier
            self.profile.save()
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.customer_tier, tier)
    
    def test_profile_str(self):
        """Test la représentation string"""
        expected = f"{self.user.get_full_name()} ({self.user.email})"
        self.assertEqual(str(self.profile), expected)
    
    def test_newsletter_preferences(self):
        """Test les préférences newsletter"""
        self.profile.subscribe_to_newsletter = False
        self.profile.receive_promotional_emails = False
        self.profile.save()
        
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.subscribe_to_newsletter)
        self.assertFalse(self.profile.receive_promotional_emails)
    
    def test_loyalty_points(self):
        """Test les points de fidélité"""
        self.profile.loyalty_points = 100
        self.profile.save()
        
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.loyalty_points, 100)
    
    def test_languages(self):
        """Test les langues supportées"""
        for lang in ['en', 'fr', 'es', 'ar']:
            self.profile.preferred_language = lang
            self.profile.save()
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.preferred_language, lang)
    
    def test_currencies(self):
        """Test les devises supportées"""
        valid_currencies = ['EUR', 'USD', 'GBP', 'XOF']
        for curr in valid_currencies:
            self.profile.preferred_currency = curr
            self.profile.save()
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.preferred_currency, curr)


class AddressModelTest(TestCase):
    """Tests pour le modèle Address (client)"""
    
    def setUp(self):
        """Créer une adresse cliente de test"""
        self.user = User.objects.create_user(
            username='customer1',
            email='customer1@example.com',
            password='pass123'
        )
        self.address = Address.objects.create(
            user=self.user,
            label='home',
            full_name='John Doe',
            phone_number='+33612345678',
            email_address='john@example.com',
            street_address='123 Main St',
            postal_code='75001',
            city='Paris',
            state_province='Île-de-France',
            country='France',
            is_default_shipping=True
        )
    
    def test_address_creation(self):
        """Test la création d'une adresse"""
        self.assertEqual(self.address.user, self.user)
        self.assertEqual(self.address.full_name, 'John Doe')
        self.assertTrue(self.address.is_default_shipping)
    
    def test_address_labels(self):
        """Test les labels d'adresse"""
        valid_labels = ['home', 'work', 'other']
        for label in valid_labels:
            self.address.label = label
            self.address.save()
            self.address.refresh_from_db()
            self.assertEqual(self.address.label, label)
    
    def test_address_str(self):
        """Test la représentation string"""
        expected = f"home - John Doe (Paris, France)"
        self.assertEqual(str(self.address), expected)
    
    def test_default_flags(self):
        """Test les drapeaux par défaut"""
        self.assertTrue(self.address.is_default_shipping)
        self.assertFalse(self.address.is_default_billing)
    
    def test_billing_address(self):
        """Test une adresse de facturation"""
        billing = Address.objects.create(
            user=self.user,
            label='other',
            full_name='Jane Doe',
            street_address='456 Other St',
            postal_code='75002',
            city='Paris',
            state_province='Île-de-France',
            country='France',
            is_default_billing=True
        )
        self.assertTrue(billing.is_default_billing)
        self.assertFalse(billing.is_default_shipping)
    
    def test_delivery_instructions(self):
        """Test les instructions de livraison"""
        self.address.delivery_instructions = 'Leave at door'
        self.address.save()
        
        self.address.refresh_from_db()
        self.assertEqual(self.address.delivery_instructions, 'Leave at door')
    
    def test_apartment_number(self):
        """Test le numéro d'appartement"""
        self.address.apartment_number = 'Apt 5B'
        self.address.save()
        
        self.address.refresh_from_db()
        self.assertEqual(self.address.apartment_number, 'Apt 5B')
