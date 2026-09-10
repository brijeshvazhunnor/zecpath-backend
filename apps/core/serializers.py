from rest_framework import serializers

from .models import User, Job


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "role",
            "is_verified",
            "created_at",
            "updated_at",
        ]


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = "__all__"