from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'role']
        extra_kwargs = {'role': {'read_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class AdminCreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'role', 'station']

    def validate(self, attrs):
        role = attrs.get('role')
        station = attrs.get('station')

        if role == 'staff' and not station:
            raise serializers.ValidationError("Staff must be assigned to a station.")
        if role == 'manager' and station:
            # Manager is linked via Station.manager OneToOne, not User.station
            attrs.pop('station', None)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role', 'station', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()