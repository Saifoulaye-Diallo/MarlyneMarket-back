"""
Checkout service for creating orders atomically.
Handles multi-seller orders, stock validation, and coupon application.
"""
from decimal import Decimal
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order, OrderItem, SellerOrder
from apps.catalog.models import Product
from apps.accounts.models import SellerProfile
from apps.orders.services.email_service import send_order_confirmation_email


@dataclass
class CheckoutError:
    """Structured error for checkout failures."""
    code: str
    message: str
    field: Optional[str] = None
    product_id: Optional[int] = None


class CheckoutService:
    """
    Service class for handling checkout process.
    Creates orders atomically with proper validation.
    """
    
    def __init__(self, user):
        self.user = user
        self.errors: List[CheckoutError] = []
    
    def create_order(
        self,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, str],
        billing_address: Optional[Dict[str, str]] = None,
        coupon_code: Optional[str] = None,
        customer_note: Optional[str] = None,
        currency: str = 'EUR'
    ) -> Optional[Order]:
        """
        Create an order from cart items.
        
        Args:
            items: List of {'product_id': int, 'quantity': int}
            shipping_address: Shipping address dict
            billing_address: Optional billing address dict
            coupon_code: Optional coupon code to apply
            customer_note: Optional customer note
            currency: Currency code (default: EUR)
        
        Returns:
            Order object if successful, None if validation fails.
            Check self.errors for details on failure.
        """
        self.errors = []
        
        # Validate items
        validated_items = self._validate_items(items)
        if self.errors:
            return None
        
        # Validate coupon if provided
        discount = Decimal('0.00')
        if coupon_code:
            discount = self._validate_and_apply_coupon(coupon_code, validated_items)
            if self.errors:
                return None
        
        # Create order atomically
        try:
            with transaction.atomic():
                order = self._create_order_atomic(
                    validated_items=validated_items,
                    shipping_address=shipping_address,
                    billing_address=billing_address or {},
                    coupon_code=coupon_code,
                    customer_note=customer_note,
                    currency=currency,
                    discount=discount
                )
                return order
        except Exception as e:
            self.errors.append(CheckoutError(
                code='CHECKOUT_FAILED',
                message=f'Failed to create order: {str(e)}'
            ))
            return None
    
    def _validate_items(self, items: List[Dict]) -> List[Dict]:
        """Validate all items and return enriched item data."""
        validated = []
        product_ids = [item['product_id'] for item in items]
        
        # Fetch all products in one query
        products = Product.objects.select_related('seller').filter(
            pk__in=product_ids
        )
        product_map = {p.pk: p for p in products}
        
        for item in items:
            product_id = item['product_id']
            quantity = item.get('quantity', 1)
            
            # Check product exists
            product = product_map.get(product_id)
            if not product:
                self.errors.append(CheckoutError(
                    code='PRODUCT_NOT_FOUND',
                    message=f'Product with ID {product_id} not found.',
                    product_id=product_id
                ))
                continue
            
            # Check product is published
            if product.status != 'published':
                self.errors.append(CheckoutError(
                    code='PRODUCT_UNAVAILABLE',
                    message=f'Product "{product.name}" is not available.',
                    product_id=product_id
                ))
                continue
            
            # Check seller is approved
            if product.seller.approval_status != 'approved':
                self.errors.append(CheckoutError(
                    code='SELLER_INACTIVE',
                    message=f'Seller for "{product.name}" is not approved.',
                    product_id=product_id
                ))
                continue
            
            # Check stock
            if product.stock < quantity:
                self.errors.append(CheckoutError(
                    code='INSUFFICIENT_STOCK',
                    message=f'Insufficient stock for "{product.name}". Available: {product.stock}',
                    product_id=product_id,
                    field='quantity'
                ))
                continue
            
            validated.append({
                'product': product,
                'quantity': quantity,
                'price': product.price,
                'seller': product.seller
            })
        
        return validated
    
    def _validate_and_apply_coupon(
        self, 
        coupon_code: str, 
        items: List[Dict]
    ) -> Decimal:
        """
        Validate coupon and calculate discount.
        Returns discount amount.
        """
        # TODO: Implement coupon validation when promotions app is ready
        # For now, return 0 discount
        return Decimal('0.00')
    
    def _create_order_atomic(
        self,
        validated_items: List[Dict],
        shipping_address: Dict,
        billing_address: Dict,
        coupon_code: Optional[str],
        customer_note: Optional[str],
        currency: str,
        discount: Decimal
    ) -> Order:
        """Create order and items within a transaction."""
        
        # Calculate subtotal
        subtotal = sum(
            Decimal(str(item['price'])) * item['quantity']
            for item in validated_items
        )
        
        # Calculate total (tax and shipping can be added later)
        tax = Decimal('0.00')  # TODO: Calculate based on region
        shipping_fee = Decimal('0.00')  # TODO: Calculate based on items/address
        total_amount = subtotal + tax + shipping_fee - discount
        
        # Create order
        order = Order.objects.create(
            user=self.user,
            subtotal=subtotal,
            tax=tax,
            shipping_fee=shipping_fee,
            discount=discount,
            total_amount=total_amount,
            currency=currency,
            coupon_code=coupon_code or '',
            shipping_address=shipping_address,
            billing_address=billing_address,
            customer_note=customer_note or '',
            status='pending',
            payment_status='unpaid'
        )
        
        # Group items by seller for SellerOrder creation
        seller_items: Dict[int, List[Dict]] = {}
        
        # Create order items and decrement stock
        for item_data in validated_items:
            product = item_data['product']
            quantity = item_data['quantity']
            price = item_data['price']
            seller = item_data['seller']
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                seller=seller,
                product=product,
                title_snapshot=product.name,
                price_snapshot=price,
                quantity=quantity
            )
            
            # Decrement stock
            product.stock -= quantity
            product.save(update_fields=['stock'])
            
            # Group by seller
            if seller.pk not in seller_items:
                seller_items[seller.pk] = []
            seller_items[seller.pk].append({
                'price': price,
                'quantity': quantity
            })
        
        # Create SellerOrder for each seller
        for seller_id, items in seller_items.items():
            seller_subtotal = sum(
                Decimal(str(i['price'])) * i['quantity'] 
                for i in items
            )
            SellerOrder.objects.create(
                seller_id=seller_id,
                order=order,
                status='pending',
                subtotal=seller_subtotal
            )
        
        # Envoyer l'email de confirmation avec tous les détails
        try:
            send_order_confirmation_email(order)
        except Exception as e:
            # Ne pas faire échouer la commande si l'email échoue
            print(f"Erreur lors de l'envoi de l'email de confirmation: {str(e)}")
        
        return order


def create_order_from_cart(payload: Dict, user) -> Dict:
    """
    Convenience function to create order from checkout payload.
    
    Args:
        payload: Validated checkout payload with items, shipping_address, etc.
        user: Authenticated user creating the order
    
    Returns:
        Dict with 'order' on success or 'errors' on failure
    """
    service = CheckoutService(user)
    
    order = service.create_order(
        items=payload['items'],
        shipping_address=payload['shipping_address'],
        billing_address=payload.get('billing_address'),
        coupon_code=payload.get('coupon_code'),
        customer_note=payload.get('customer_note'),
        currency=payload.get('currency', 'EUR')
    )
    
    if order:
        return {'order': order}
    
    return {
        'errors': [
            {
                'code': e.code,
                'message': e.message,
                'field': e.field,
                'product_id': e.product_id
            }
            for e in service.errors
        ]
    }
