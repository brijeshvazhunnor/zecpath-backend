from rest_framework import serializers

from .models import User, Job, Candidate, Employer


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


class CandidateProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Candidate

        fields = [
            "id",
            "full_name",
            "email",
            "skills",
            "education",
            "experience",
            "expected_salary",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "email",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_expected_salary(self, value):

        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Expected salary cannot be negative."
            )

        return value


class EmployerProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employer

        fields = [
            "id",
            "company_name",
            "domain",
            "company_size",
            "is_verified",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "is_verified",
            "is_active",
            "created_at",
            "updated_at",
        ]