from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView as JWTTokenRefreshView

from apps.accounts.views import (
    TokenObtainView, TokenRefreshView, MeView, SellerProfileViewSet,
    LoginView, RegisterView, SellerRegisterView, AdminUserListView, AdminSellerListView,
    AdminProductListView, LogoutView
)
from apps.accounts.api_seller_with_user import SellerWithUserCreateView

router = SimpleRouter()
router.register(r'sellers', SellerProfileViewSet, basename='seller-profile')

urlpatterns = [
    # JWT Token endpoints
    path('token/', TokenObtainView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Login/Register/Logout endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('register/seller/', SellerRegisterView.as_view(), name='seller_register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # User endpoints
    path('me/', MeView.as_view(), name='me'),
    
    # Seller creation with user
    path('sellers-with-user/', SellerWithUserCreateView.as_view(), name='sellers_with_user_create'),
    
    # Router endpoints
    path('', include(router.urls)),
]
