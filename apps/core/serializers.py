from rest_framework import serializers

from .models import User, Job, Candidate, Employer, Application


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


import os

from rest_framework import serializers

from .models import Candidate, Employer, Resume


class ResumeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Resume

        fields = [
            "id",
            "file",
            "original_filename",
            "file_size",
            "uploaded_at",
            "updated_at",
            "is_active",
        ]

        read_only_fields = [
            "id",
            "original_filename",
            "file_size",
            "uploaded_at",
            "updated_at",
            "is_active",
        ]

    def validate_file(self, value):

        # Maximum file size: 5 MB
        max_size = 5 * 1024 * 1024

        if value.size > max_size:
            raise serializers.ValidationError(
                "Resume file size cannot exceed 5 MB."
            )

        # Allowed extensions
        allowed_extensions = [
            ".pdf",
            ".docx",
        ]

        extension = os.path.splitext(
            value.name
        )[1].lower()

        if extension not in allowed_extensions:
            raise serializers.ValidationError(
                "Only PDF and DOCX files are allowed."
            )

        return value


class ApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application
        fields = [
            "id",
            "job",
            "candidate",
            "applied_at",
            "status",
        ]

        read_only_fields = [
            "id",
            "candidate",
            "applied_at",
        ]