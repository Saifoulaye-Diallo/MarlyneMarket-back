from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_preference import UserPreferenceViewSet

router = DefaultRouter()
router.register(r'preferences', UserPreferenceViewSet, basename='userpreference')

urlpatterns = [
    path('', include(router.urls)),
]
