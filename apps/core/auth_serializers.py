from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "phone",
            "role",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):

    # IMPORTANT:
    # Tell SimpleJWT that this serializer accepts email
    # instead of the default username.
    username_field = "email"

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):

        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No active account found with the given credentials"
            )

        # Your User model still authenticates using username,
        # so authenticate using the user's username internally.
        user = authenticate(
            username=user.username,
            password=password
        )

        if user is None or not user.is_active:
            raise serializers.ValidationError(
                "No active account found with the given credentials"
            )

        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }