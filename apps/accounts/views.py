from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from apps.accounts.models import User, SellerProfile
from apps.accounts.serializers import (
    UserSerializer, UserDetailSerializer, TokenObtainSerializer,
    SellerProfileSerializer, SellerProfileDetailSerializer
)
from apps.accounts.permissions import IsSuperAdmin, IsSellerOrSuperAdmin, IsOwnSellerProfile
from apps.customers.models import CustomerProfile


class TokenObtainView(views.APIView):
    """Authenticate user and return JWT tokens."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenObtainSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshView(views.APIView):
    """Refresh JWT access token."""
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'access': str(refresh.access_token)
            })
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MeView(views.APIView):
    """Get current user information."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)


class LoginView(views.APIView):
    """Customer/Seller login endpoint - returns JWT tokens."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'detail': 'Username and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {'detail': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class RegisterView(views.APIView):
    """Customer registration endpoint."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')
        
        # Validation
        if not all([username, email, password, password_confirm]):
            return Response(
                {'detail': 'All fields required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if password != password_confirm:
            return Response(
                {'detail': 'Passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response(
                {'detail': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {'detail': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='customer',
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', ''),
            phone_number=request.data.get('phone_number', '')
        )
        
        # Create customer profile with additional fields
        CustomerProfile.objects.create(
            user=user,
            date_of_birth=request.data.get('date_of_birth'),
            preferred_language=request.data.get('preferred_language', 'en'),
            preferred_currency=request.data.get('preferred_currency', 'USD')
        )
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class SellerRegisterView(views.APIView):
    """Seller registration endpoint."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')
        shop_name = request.data.get('shop_name')
        
        # Validation
        if not all([username, email, password, password_confirm, shop_name]):
            return Response(
                {'detail': 'All fields required (username, email, password, password_confirm, shop_name)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if password != password_confirm:
            return Response(
                {'detail': 'Passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response(
                {'detail': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {'detail': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='seller',
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', ''),
            phone_number=request.data.get('phone_number', '')
        )
        
        # Create seller profile
        SellerProfile.objects.create(
            user=user,
            shop_name=shop_name,
            shop_description=request.data.get('shop_description', ''),
            business_type=request.data.get('business_type', 'individual'),
            country=request.data.get('country', ''),
            primary_phone=request.data.get('phone_number', ''),
            approval_status='pending'
        )
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class SellerProfileViewSet(viewsets.ModelViewSet):
    """
    Admin viewset for managing seller profiles.
    Super admin only.
    """
    queryset = SellerProfile.objects.select_related('user')
    serializer_class = SellerProfileSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SellerProfileDetailSerializer
        return SellerProfileSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return SellerProfile.objects.select_related('user').all()
        return SellerProfile.objects.none()

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a seller profile."""
        seller = self.get_object()
        seller.status = 'active'
        seller.save()
        return Response(
            {'detail': 'Seller activated', 'status': seller.status},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a seller profile."""
        seller = self.get_object()
        seller.status = 'suspended'
        seller.save()
        return Response(
            {'detail': 'Seller suspended', 'status': seller.status},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending seller profiles."""
        sellers = SellerProfile.objects.filter(status='pending').select_related('user')
        page = self.paginate_queryset(sellers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(sellers, many=True)
        return Response(serializer.data)

class CustomerProfileDetailView(views.APIView):
    """View for accessing customer profile."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        """Get customer profile."""
        try:
            from apps.customers.models import CustomerProfile
            profile = CustomerProfile.objects.get(id=id)
            
            # Check access: user can only view their own profile
            if profile.user != request.user and not request.user.is_staff:
                return Response(
                    {'detail': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from apps.customers.serializers import CustomerProfileSerializer
            serializer = CustomerProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request, id):
        """Partially update customer profile."""
        return self.put(request, id)
    
    def put(self, request, id):
        """Update customer profile."""
        try:
            from apps.customers.models import CustomerProfile
            profile = CustomerProfile.objects.get(id=id)
            
            # Check access: user can only update their own profile
            if profile.user != request.user and not request.user.is_staff:
                return Response(
                    {'detail': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from apps.customers.serializers import CustomerProfileSerializer
            serializer = CustomerProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )


class SellerProfileDetailView(views.APIView):
    """View for accessing seller profile."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        """Get seller profile."""
        try:
            profile = SellerProfile.objects.get(id=id)
            serializer = SellerProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SellerProfile.DoesNotExist:
            return Response(
                {'detail': 'Seller profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request, id):
        """Partially update seller profile.""" 
        return self.put(request, id)
    
    def put(self, request, id):
        """Update seller profile."""
        try:
            profile = SellerProfile.objects.get(id=id)
            
            # Check access: seller can only update their own profile
            if profile.user != request.user and not request.user.is_staff:
                return Response(
                    {'detail': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = SellerProfileDetailSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SellerProfile.DoesNotExist:
            return Response(
                {'detail': 'Seller profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminUserListView(views.APIView):
    """Admin view to list all users."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all users - admin only."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        users = User.objects.all().values('id', 'username', 'email', 'is_staff', 'is_active')
        return Response(list(users), status=status.HTTP_200_OK)


class AdminSellerListView(views.APIView):
    """Admin view to list all sellers."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all sellers - admin only."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        sellers = SellerProfile.objects.all().select_related('user').values(
            'id', 'user_id', 'shop_name', 'approval_status'
        )
        return Response(list(sellers), status=status.HTTP_200_OK)


class AdminProductListView(views.APIView):
    """Admin view to list all products."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all products - admin only."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        from apps.catalog.models import Product
        products = Product.objects.all().select_related('seller', 'category').values(
            'id', 'name', 'price', 'status', 'seller_id'
        )
        return Response(list(products), status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    """Logout endpoint to invalidate JWT tokens."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Logout user by blacklisting their access and refresh tokens."""
        try:
            from .models import BlacklistedAccessToken
            
            # Blacklist refresh token if provided
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Blacklist access token from Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if auth_header and auth_header.startswith('Bearer '):
                access_token = auth_header.split(' ')[1]
                try:
                    from rest_framework_simplejwt.tokens import UntypedToken
                    
                    # Verify and get token
                    token = UntypedToken(access_token)
                    jti = token['jti']
                    
                    # Blacklist the access token in our custom model
                    BlacklistedAccessToken.objects.get_or_create(
                        jti=jti,
                        defaults={'user': request.user}
                    )
                except:
                    pass  # Invalid token, ignore
            
            return Response(
                {'detail': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'detail': 'Successfully logged out'},  # Don't reveal errors
                status=status.HTTP_200_OK
            )
