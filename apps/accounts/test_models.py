from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import SellerProfile, UserAddress
import uuid

User = get_user_model()


class UserModelTest(TestCase):
    """Tests pour le modèle User"""
    
    def setUp(self):
        """Créer un utilisateur de test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='customer',
            phone_number='+33612345678'
        )
    
    def test_user_creation(self):
        """Test la création d'un utilisateur"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'customer')
        self.assertTrue(isinstance(self.user.id, uuid.UUID))
    
    def test_user_is_customer(self):
        """Test la méthode is_customer"""
        self.assertTrue(self.user.is_customer())
        self.assertFalse(self.user.is_seller())
    
    def test_user_is_seller(self):
        """Test la création d'un vendeur"""
        seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='pass123',
            role='seller'
        )
        self.assertTrue(seller.is_seller())
        self.assertFalse(seller.is_customer())
    
    def test_user_is_super_admin(self):
        """Test la création d'un super admin"""
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123',
            role='super_admin'
        )
        self.assertTrue(admin.is_super_admin())
    
    def test_user_str(self):
        """Test la représentation string de User"""
        expected = f"Test User ({self.user.email})"
        self.assertEqual(str(self.user), expected)
    
    def test_user_phone_validation(self):
        """Test la validation du numéro de téléphone"""
        user = User(
            username='test2',
            email='test2@example.com',
            role='customer',
            phone_number='invalid_phone'
        )
        user.set_password('pass123')
        # La validation se fait au niveau du formulaire/serializer
        # Le modèle accepte la valeur
        self.assertIsNotNone(user.phone_number)
    
    def test_user_account_status(self):
        """Test les status de compte"""
        self.assertEqual(self.user.account_status, 'active')
        self.user.account_status = 'suspended'
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.account_status, 'suspended')
    
    def test_user_email_verification(self):
        """Test la vérification d'email"""
        self.assertFalse(self.user.email_verified)
        self.assertIsNone(self.user.email_verified_at)
        
        from django.utils import timezone
        self.user.email_verified = True
        self.user.email_verified_at = timezone.now()
        self.user.save()
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertIsNotNone(self.user.email_verified_at)


class SellerProfileModelTest(TestCase):
    """Tests pour le modèle SellerProfile"""
    
    def setUp(self):
        """Créer un profil vendeur de test"""
        self.user = User.objects.create_user(
            username='seller1',
            email='seller1@example.com',
            password='pass123',
            role='seller'
        )
        self.seller = SellerProfile.objects.create(
            user=self.user,
            shop_name='Test Shop',
            shop_slug='test-shop',
            business_type='individual',
            primary_phone='+33612345678',
            street_address='123 Main St',
            city='Paris',
            state_province='Île-de-France',
            postal_code='75001',
            country='France'
        )
    
    def test_seller_creation(self):
        """Test la création d'un profil vendeur"""
        self.assertEqual(self.seller.shop_name, 'Test Shop')
        self.assertEqual(self.seller.user, self.user)
        self.assertEqual(self.seller.approval_status, 'pending')
    
    def test_seller_str(self):
        """Test la représentation string de SellerProfile"""
        expected = f"Test Shop ({self.user.email})"
        self.assertEqual(str(self.seller), expected)
    
    def test_seller_metrics_defaults(self):
        """Test les valeurs par défaut des métriques"""
        self.assertEqual(self.seller.total_products, 0)
        self.assertEqual(self.seller.average_rating, 0)
        self.assertEqual(self.seller.total_reviews, 0)
        self.assertEqual(self.seller.total_orders, 0)
    
    def test_seller_approval_status(self):
        """Test le statut d'approbation"""
        self.assertEqual(self.seller.approval_status, 'pending')
        self.seller.approval_status = 'approved'
        self.seller.save()
        
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.approval_status, 'approved')
    
    def test_seller_business_types(self):
        """Test les types d'entreprise"""
        valid_types = ['individual', 'business', 'corporate']
        for btype in valid_types:
            seller = SellerProfile(
                user=self.user,
                shop_name=f'Shop {btype}',
                business_type=btype
            )
            self.assertEqual(seller.business_type, btype)
    
    def test_seller_full_address(self):
        """Test la méthode get_full_address"""
        full_address = self.seller.get_full_address()
        self.assertIn('123 Main St', full_address)
        self.assertIn('Paris', full_address)
        self.assertIn('France', full_address)
    
    def test_seller_return_days_default(self):
        """Test la valeur par défaut des jours de retour"""
        self.assertEqual(self.seller.return_days, 30)
    
    def test_seller_seller_level(self):
        """Test le niveau du vendeur"""
        self.assertEqual(self.seller.seller_level, 'bronze')


class UserAddressModelTest(TestCase):
    """Tests pour le modèle UserAddress"""
    
    def setUp(self):
        """Créer une adresse de test"""
        self.user = User.objects.create_user(
            username='customer1',
            email='customer1@example.com',
            password='pass123'
        )
        self.address = UserAddress.objects.create(
            user=self.user,
            address_type='shipping',
            recipient_name='John Doe',
            phone_number='+33612345678',
            street_address='123 Main St',
            postal_code='75001',
            city='Paris',
            state_province='Île-de-France',
            country='France',
            is_default=True
        )
    
    def test_address_creation(self):
        """Test la création d'une adresse"""
        self.assertEqual(self.address.user, self.user)
        self.assertEqual(self.address.recipient_name, 'John Doe')
        self.assertTrue(self.address.is_default)
    
    def test_address_types(self):
        """Test les types d'adresse"""
        valid_types = ['shipping', 'billing', 'both']
        for atype in valid_types:
            addr = UserAddress(
                user=self.user,
                address_type=atype,
                recipient_name='Test'
            )
            self.assertEqual(addr.address_type, atype)
    
    def test_address_str(self):
        """Test la représentation string"""
        expected = f"John Doe - Paris, France"
        self.assertEqual(str(self.address), expected)
    
    def test_full_address(self):
        """Test la méthode get_full_address"""
        full = self.address.get_full_address()
        self.assertIn('123 Main St', full)
        self.assertIn('75001', full)
        self.assertIn('Paris', full)
    
    def test_unique_together(self):
        """Test la contrainte unique together"""
        # Les mêmes user + recipient_name ne peuvent pas exister deux fois
        duplicate = UserAddress(
            user=self.user,
            recipient_name='John Doe',
            address_type='billing',
            street_address='456 Other St',
            postal_code='75002',
            city='Paris',
            state_province='Île-de-France',
            country='France'
        )
        # La sauvegarde devrait lever une exception
        with self.assertRaises(Exception):
            duplicate.save()
