from rest_framework import status, views
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from apps.accounts.models import SellerProfile
from apps.accounts.serializers import SellerProfileSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser

User = get_user_model()

class SellerWithUserCreateView(views.APIView):
    """
    Create a seller (user + seller profile) in one call.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        user_data = {
            'email': request.data.get('email'),
            'username': request.data.get('username'),
            'password': request.data.get('password'),
            'first_name': request.data.get('first_name', ''),
            'last_name': request.data.get('last_name', ''),
            'role': 'seller',
        }
        user_serializer = UserSerializer(data=user_data)
        if not user_serializer.is_valid():
            return Response({'user_errors': user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        user = user_serializer.save()
        user.set_password(user_data['password'])
        user.save()

        profile_data = {
            'shop_name': request.data.get('shop_name', user.get_full_name()),
            'shop_description': request.data.get('shop_description', ''),
            'phone': request.data.get('phone', ''),
            'address': request.data.get('address', ''),
            'city': request.data.get('city', ''),
            'country': request.data.get('country', ''),
            'status': request.data.get('status', 'active'),
        }
        profile_serializer = SellerProfileSerializer(data=profile_data)
        if not profile_serializer.is_valid():
            user.delete()
            return Response({'profile_errors': profile_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        # Set the user directly on the profile instance since the serializer field is read_only
        profile = profile_serializer.save(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'seller_profile': SellerProfileSerializer(profile).data
        }, status=status.HTTP_201_CREATED)
