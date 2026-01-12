from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser
from .models import BlacklistedAccessToken


class CustomJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication that checks for blacklisted access tokens"""
    
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        # Validate token format and signature
        validated_token = self.get_validated_token(raw_token)
        
        # Check if access token is blacklisted
        try:
            jti = validated_token.payload.get('jti')
            if jti and BlacklistedAccessToken.objects.filter(jti=jti).exists():
                raise InvalidToken('Token is blacklisted')
        except (KeyError, AttributeError):
            pass
        
        user = self.get_user(validated_token)
        return (user, validated_token)