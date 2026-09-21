from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EMPLOYER = "employer", "Employer"
        CANDIDATE = "candidate", "Candidate"

    email = models.EmailField(unique=True)

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CANDIDATE
    )

    is_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_verified"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.email


class Employer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employer"
    )

    company_name = models.CharField(
        max_length=200,
        blank=True
    )

    domain = models.CharField(
        max_length=200,
        blank=True
    )

    company_size = models.CharField(
        max_length=100,
        blank=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.company_name or self.user.email


class Candidate(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="candidate"
    )

    full_name = models.CharField(
        max_length=200
    )

    email = models.EmailField()

    skills = models.TextField(
        blank=True
    )

    education = models.TextField(
        blank=True
    )

    experience = models.TextField(
        blank=True
    )

    expected_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.full_name


class Job(models.Model):

    class JobType(models.TextChoices):
        FULL_TIME = "full_time", "Full Time"
        PART_TIME = "part_time", "Part Time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"
        TEMPORARY = "temporary", "Temporary"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name="jobs"
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    required_skills = models.TextField()

    experience = models.CharField(
        max_length=100
    )

    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    location = models.CharField(
        max_length=200
    )

    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        default=JobType.FULL_TIME
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["location"]),
            models.Index(fields=["experience"]),
            models.Index(fields=["job_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["featured"]),
            models.Index(fields=["status", "featured"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title


class Application(models.Model):

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    # Snapshot of the resume used when the application was submitted.
    # This preserves the resume metadata even if the candidate
    # later updates their current resume.
    resume_snapshot = models.JSONField(
        default=dict
    )

    applied_at = models.DateTimeField(
        auto_now_add=True
    )

    STATUS_CHOICES = [
        ("applied", "Applied"),
        ("shortlisted", "Shortlisted"),
        ("interview_scheduled", "Interview Scheduled"),
        ("rejected", "Rejected"),
        ("selected", "Selected"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="applied"
    )

    VALID_STATUS_TRANSITIONS = {
        "applied": [
            "shortlisted",
            "rejected",
        ],
        "shortlisted": [
            "interview_scheduled",
            "rejected",
        ],
        "interview_scheduled": [
            "selected",
            "rejected",
        ],
        "rejected": [],
        "selected": [],
    }

    LOCKED_STATUSES = {
        "rejected",
        "selected",
    }

    def can_transition_to(self, new_status):
        if self.status in self.LOCKED_STATUSES:
            return False

        return new_status in self.VALID_STATUS_TRANSITIONS.get(
            self.status,
            []
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job"],
                name="unique_candidate_job_application"
            ),
        ]

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["applied_at"]),
            models.Index(fields=["candidate", "applied_at"]),
            models.Index(fields=["job", "status"]),
        ]

    def __str__(self):
        return f"{self.candidate} - {self.job}"


class ApplicationStatusHistory(models.Model):

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="status_history"
    )

    old_status = models.CharField(
        max_length=20,
        blank=True
    )

    new_status = models.CharField(
        max_length=20
    )

    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="application_status_changes"
    )

    action = models.CharField(
        max_length=100,
        blank=True
    )

    changed_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["changed_at"]

        indexes = [
            models.Index(
                fields=["application", "changed_at"]
            ),
            models.Index(
                fields=["changed_by", "changed_at"]
            ),
        ]

    def __str__(self):
        return (
            f"Application {self.application_id}: "
            f"{self.old_status} -> {self.new_status}"
        )


class Resume(models.Model):

    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name="resume"
    )

    file = models.FileField(
        upload_to="resumes/"
    )

    original_filename = models.CharField(
        max_length=255
    )

    file_size = models.PositiveIntegerField()

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.candidate.full_name} - {self.original_filename}"