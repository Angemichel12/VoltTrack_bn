from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from .models import User
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .exceptions import success_response, error_response


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes =[]

    @extend_schema(
        tags=['Auth'],
        summary='Register a new staff account',
        request=RegisterSerializer,
        responses={201: UserSerializer},
    )
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

    @extend_schema(
        tags=['Auth'],
        summary='Log in with phone number and password',
        request=LoginSerializer,
        responses={200: inline_serializer(
            name='LoginResponse',
            fields={
                'id': serializers.IntegerField(),
                'name': serializers.CharField(),
                'phone_number': serializers.CharField(),
                'role': serializers.CharField(),
                'access': serializers.CharField(),
                'refresh': serializers.CharField(),
            }
        )},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        user = authenticate(
            phone_number=serializer.validated_data['phone_number'],
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

    @extend_schema(
        tags=['Auth'],
        summary='Exchange a refresh token for a new access token',
        request=inline_serializer(
            name='TokenRefreshRequest',
            fields={'refresh': serializers.CharField()}
        ),
        responses={200: inline_serializer(
            name='TokenRefreshResponse',
            fields={'access': serializers.CharField(), 'refresh': serializers.CharField()}
        )},
    )
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


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Auth'],
        summary='Log out (blocked while a shift is open)',
        request=inline_serializer(
            name='LogoutRequest',
            fields={'refresh': serializers.CharField()}
        ),
        responses={200: inline_serializer(name='LogoutResponse', fields={'message': serializers.CharField()})},
    )
    def post(self, request):
        from chargers.models import ShiftRecord

        if request.user.role == 'staff' and ShiftRecord.get_open_for(request.user):
            return error_response(message="End your shift before logging out.", status_code=400)

        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return error_response(message="Refresh token required")
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return error_response(message="Invalid or expired refresh token", status_code=401)

        return success_response(message="Logged out successfully")


def _get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}