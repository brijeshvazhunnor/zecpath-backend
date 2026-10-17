from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User,
    Employer,
    Candidate,
    Job,
    Application,
    SavedJob,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        (
            "Zecpath Information",
            {
                "fields": (
                    "phone",
                    "role",
                    "is_verified",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_display = (
        "username",
        "email",
        "role",
        "is_verified",
        "is_active",
    )

    list_filter = (
        "role",
        "is_verified",
        "is_active",
    )


@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):

    list_display = (
        "company_name",
        "user",
    )

    search_fields = (
        "company_name",
        "user__email",
    )


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "email",
        "user",
    )

    search_fields = (
        "full_name",
        "email",
        "user__email",
    )


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "employer",
        "location",
        "experience",
        "created_at",
    )

    list_filter = (
        "location",
        "experience",
    )

    search_fields = (
        "title",
        "description",
        "employer__company_name",
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):

    list_display = (
        "job",
        "candidate",
        "status",
        "applied_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "job__title",
        "candidate__full_name",
        "candidate__email",
    )


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):

    list_display = (
        "candidate",
        "job",
        "saved_at",
    )

    list_filter = (
        "saved_at",
    )

    search_fields = (
        "candidate__full_name",
        "candidate__email",
        "job__title",
    )