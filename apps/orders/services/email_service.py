"""
Email service for sending order notifications.
"""
from decimal import Decimal
from typing import Dict
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from apps.orders.models import Order, EmailLog


def send_order_confirmation_email(order: Order) -> bool:
    """
    Envoie un email de confirmation de commande avec tous les détails.
    
    Args:
        order: L'objet Order à envoyer par email
        
    Returns:
        True si l'email a été envoyé avec succès, False sinon
    """
    user = order.user
    
    # Préparer les données de la commande
    order_items = []
    for item in order.items.select_related('product', 'seller'):
        order_items.append({
            'title': item.title_snapshot,
            'quantity': item.quantity,
            'price': item.price_snapshot,
            'line_total': item.line_total,
            'seller': item.seller.shop_name if item.seller else 'N/A'
        })
    
    # Créer le contenu de l'email
    subject = f'Confirmation de commande #{order.reference}'
    
    # Message en texte brut
    message = f"""
Bonjour {user.get_full_name()},

Nous avons bien reçu votre commande #{order.reference}.

INFORMATIONS CLIENT:
Nom: {user.get_full_name()}
Email: {user.email}
Téléphone: {user.phone if hasattr(user, 'phone') else 'N/A'}

ADRESSE DE LIVRAISON:
{order.shipping_address.get('full_name', 'N/A')}
{order.shipping_address.get('address1', '')}
{order.shipping_address.get('address2', '')}
{order.shipping_address.get('postal_code', '')} {order.shipping_address.get('city', '')}
{order.shipping_address.get('country', '')}
Téléphone: {order.shipping_address.get('phone', 'N/A')}

DÉTAILS DE LA COMMANDE:
"""
    
    for item in order_items:
        message += f"\n- {item['title']} x {item['quantity']}"
        message += f"\n  Prix unitaire: {item['price']} {order.currency}"
        message += f"\n  Total: {item['line_total']} {order.currency}"
        message += f"\n  Vendeur: {item['seller']}\n"
    
    message += f"""
RÉSUMÉ:
Sous-total: {order.subtotal} {order.currency}
Frais de livraison: {order.shipping_fee} {order.currency}
Taxes: {order.tax} {order.currency}
"""
    
    if order.discount and order.discount > 0:
        message += f"Remise: -{order.discount} {order.currency}\n"
    
    message += f"""
TOTAL À PAYER: {order.total_amount} {order.currency}

"""
    
    if order.customer_note:
        message += f"Note du client: {order.customer_note}\n\n"
    
    message += f"""
Pour effectuer le paiement, veuillez nous contacter.

Merci pour votre confiance!

L'équipe Marketplace
"""
    
    # Destinataires
    recipient_list = [user.email]
    
    # Ajouter l'admin en copie
    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
    if admin_email:
        recipient_list.append(admin_email)
    
    # Créer le log d'email en statut pending
    email_log = EmailLog.objects.create(
        order=order,
        recipient=user.email,
        subject=subject,
        body=message,
        status='pending'
    )
    
    try:
        # Envoyer l'email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        # Mettre à jour le statut à 'sent'
        email_log.status = 'sent'
        email_log.save()
        
        return True
        
    except Exception as e:
        # Enregistrer l'erreur
        email_log.status = 'failed'
        email_log.error_message = str(e)
        email_log.save()
        
        print(f"Erreur lors de l'envoi de l'email: {str(e)}")
        return False
