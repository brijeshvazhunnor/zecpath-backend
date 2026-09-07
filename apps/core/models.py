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

    def __str__(self):
        return self.email


class Employer(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employer"
    )

    company_name = models.CharField(
        max_length=200
    )

    def __str__(self):
        return self.company_name


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

    def __str__(self):
        return self.full_name


class Job(models.Model):

    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name="jobs"
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    location = models.CharField(
        max_length=200
    )

    required_skills = models.TextField()

    experience = models.CharField(
        max_length=100
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

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

    applied_at = models.DateTimeField(
        auto_now_add=True
    )

    STATUS_CHOICES = [
        ("applied", "Applied"),
        ("shortlisted", "Shortlisted"),
        ("rejected", "Rejected"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="applied"
    )

    def __str__(self):
        return f"{self.candidate} - {self.job}"