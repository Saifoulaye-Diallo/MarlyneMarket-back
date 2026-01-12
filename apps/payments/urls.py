"""
URL configuration for payments app.
"""
from django.urls import path
from apps.payments.views import (
    CreatePaymentIntentView,
    StripeWebhookView,
    PaymentListView,
)

urlpatterns = [
    path('', PaymentListView.as_view(), name='payment-list'),
    path('create-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('webhook/stripe/', StripeWebhookView.as_view(), name='stripe-webhook-alt'),
]
