from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .exceptions import success_response, error_response


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes =[]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            # Default registration creates staff users
            user = serializer.save(role='staff')
            tokens = _get_tokens(user)
            return success_response(
                data={**UserSerializer(user).data, **tokens},
                message="Registration successful",
                status_code=201
            )
        return error_response(message="Registration failed", errors=serializer.errors)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes =[]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        if not user:
            return error_response(message="Invalid credentials", status_code=401)
        if not user.is_active:
            return error_response(message="Account is inactive", status_code=403)

        tokens = _get_tokens(user)
        return success_response(
            data={**UserSerializer(user).data, **tokens},
            message="Login successful"
        )


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes =[]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return error_response(message="Refresh token required")
        try:
            token = RefreshToken(refresh_token)
            return success_response(data={
                'access': str(token.access_token),
                'refresh': str(token)
            })
        except Exception:
            return error_response(message="Invalid or expired refresh token", status_code=401)


def _get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}