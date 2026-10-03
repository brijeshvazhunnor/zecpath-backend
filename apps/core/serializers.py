from rest_framework import serializers

from .models import (
    User,
    Employer,
    Candidate,
    Job,
    Application,
    Resume,
    ApplicationStatusHistory,
    SavedJob,
    AuditLog,
    ModerationFlag,
)

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "phone",
            "role",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "username",
            "email",
            "phone",
            "role",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
        ]


class JobSerializer(serializers.ModelSerializer):

    class Meta:
        model = Job

        fields = [
            "id",
            "employer",
            "title",
            "description",
            "required_skills",
            "experience",
            "salary_min",
            "salary_max",
            "location",
            "job_type",
            "status",
            "featured",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "employer",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):

        salary_min = attrs.get("salary_min")
        salary_max = attrs.get("salary_max")

        if (
            salary_min is not None
            and salary_max is not None
            and salary_min > salary_max
        ):
            raise serializers.ValidationError(
                {
                    "salary": (
                        "Minimum salary cannot be greater "
                        "than maximum salary."
                    )
                }
            )

        if salary_min is not None and salary_min < 0:
            raise serializers.ValidationError(
                {
                    "salary_min": "Minimum salary cannot be negative."
                }
            )

        if salary_max is not None and salary_max < 0:
            raise serializers.ValidationError(
                {
                    "salary_max": "Maximum salary cannot be negative."
                }
            )

        return attrs


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
            "resume_snapshot",
            "applied_at",
            "status",
        ]

        read_only_fields = [
            "id",
            "candidate",
            "resume_snapshot",
            "applied_at",
        ]

class EmployerApplicantSerializer(serializers.ModelSerializer):

    candidate_name = serializers.CharField(
        source="candidate.full_name",
        read_only=True
    )

    candidate_email = serializers.CharField(
        source="candidate.email",
        read_only=True
    )

    candidate_skills = serializers.CharField(
        source="candidate.skills",
        read_only=True
    )

    job_title = serializers.CharField(
        source="job.title",
        read_only=True
    )

    class Meta:
        model = Application

        fields = [
            "id",
            "job",
            "job_title",
            "candidate",
            "candidate_name",
            "candidate_email",
            "candidate_skills",
            "status",
            "applied_at",
        ]

        read_only_fields = fields

class ApplicationStatusHistorySerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = ApplicationStatusHistory

        fields = [
            "id",
            "application",
            "old_status",
            "new_status",
            "changed_by",
            "action",
            "changed_at",
        ]

        read_only_fields = [
            "id",
            "application",
            "old_status",
            "new_status",
            "changed_by",
            "action",
            "changed_at",
        ]

class SavedJobSerializer(serializers.ModelSerializer):

    job_title = serializers.CharField(
        source="job.title",
        read_only=True
    )

    company_name = serializers.CharField(
        source="job.employer.company_name",
        read_only=True
    )

    job_location = serializers.CharField(
        source="job.location",
        read_only=True
    )

    job_type = serializers.CharField(
        source="job.job_type",
        read_only=True
    )

    class Meta:
        model = SavedJob
        fields = [
            "id",
            "job",
            "job_title",
            "company_name",
            "job_location",
            "job_type",
            "saved_at",
        ]

        read_only_fields = [
            "id",
            "job_title",
            "company_name",
            "job_location",
            "job_type",
            "saved_at",
        ]

class CandidateApplicationSerializer(serializers.ModelSerializer):

    job_title = serializers.CharField(
        source="job.title",
        read_only=True
    )

    company_name = serializers.CharField(
        source="job.employer.company_name",
        read_only=True
    )

    job_location = serializers.CharField(
        source="job.location",
        read_only=True
    )

    class Meta:
        model = Application
        fields = [
            "id",
            "job",
            "job_title",
            "company_name",
            "job_location",
            "status",
            "applied_at",
        ]

        read_only_fields = fields


class CandidateApplicationTimelineSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = ApplicationStatusHistory
        fields = [
            "id",
            "old_status",
            "new_status",
            "action",
            "changed_at",
        ]

        read_only_fields = fields


class CandidateRecommendationSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="employer.company_name",
        read_only=True
    )
    match_score = serializers.FloatField(read_only=True)
    matched_skills = serializers.ListField(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "company_name",
            "description",
            "required_skills",
            "experience",
            "location",
            "job_type",
            "salary_min",
            "salary_max",
            "match_score",
            "matched_skills",
            "created_at",
        ]
        read_only_fields = fields


class AuditLogSerializer(serializers.ModelSerializer):

    admin_email = serializers.CharField(
        source="admin.email",
        read_only=True
    )

    class Meta:
        model = AuditLog

        fields = [
            "id",
            "admin",
            "admin_email",
            "action",
            "target_type",
            "target_id",
            "description",
            "created_at",
        ]

        read_only_fields = fields


class ModerationFlagSerializer(serializers.ModelSerializer):

    user_email = serializers.CharField(
        source="user.email",
        read_only=True
    )

    flagged_by_email = serializers.CharField(
        source="flagged_by.email",
        read_only=True
    )

    class Meta:
        model = ModerationFlag

        fields = [
            "id",
            "user",
            "user_email",
            "flagged_by",
            "flagged_by_email",
            "reason",
            "status",
            "created_at",
            "reviewed_at",
        ]

        read_only_fields = [
            "id",
            "user_email",
            "flagged_by",
            "flagged_by_email",
            "created_at",
            "reviewed_at",
        ]


from rest_framework import serializers


class ResumeParseSerializer(serializers.Serializer):
    """
    Serializer for resume upload and parsing.
    """

    file = serializers.FileField(required=True)

    def validate_file(self, value):
        """
        Basic file validation.
        """

        max_size = 5 * 1024 * 1024  # 5 MB

        if value.size > max_size:
            raise serializers.ValidationError(
                "Resume file size must not exceed 5 MB."
            )

        filename = value.name.lower()

        if not filename.endswith((".pdf", ".docx")):
            raise serializers.ValidationError(
                "Only PDF and DOCX files are supported."
            )

        return value