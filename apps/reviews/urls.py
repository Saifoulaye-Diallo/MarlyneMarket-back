"""
URL configuration for reviews app.
"""
from django.urls import path, include
from rest_framework.routers import SimpleRouter

from apps.reviews.views import (
    PublicReviewViewSet,
    CustomerReviewViewSet,
    AdminReviewViewSet,
    ReviewHelpfulView,
)

public_router = SimpleRouter()
public_router.register(r'', PublicReviewViewSet, basename='public-review')

customer_router = SimpleRouter()
customer_router.register(r'', CustomerReviewViewSet, basename='customer-review')

admin_router = SimpleRouter()
admin_router.register(r'', AdminReviewViewSet, basename='admin-review')

urlpatterns = [
    path('', include(public_router.urls)),
    path('my/', include(customer_router.urls)),
    path('admin/', include(admin_router.urls)),
    path('<int:review_id>/helpful/', ReviewHelpfulView.as_view(), name='review-helpful'),
]
