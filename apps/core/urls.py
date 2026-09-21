from django.urls import path

from .views import (
    JobListAPIView,
    JobCreateAPIView,
    FeaturedJobListAPIView,
    LatestJobListAPIView,
    UserTestAPIView,
    SignupAPIView,
    LoginAPIView,
    LogoutAPIView,
    CandidateProfileAPIView,
    EmployerProfileAPIView,
    ResumeUploadAPIView,
    ResumeAPIView,
    JobUpdateAPIView,
    JobStatusAPIView,
    ApplicationListAPIView,
    ApplicationDetailAPIView,
    JobApplicationCreateAPIView,
    ApplicationStatusUpdateAPIView,
    ApplicationStatusHistoryAPIView,
)

from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    # Existing APIs
    path("jobs/create/", JobCreateAPIView.as_view(), name="job-create"),
    path("users/", UserTestAPIView.as_view(), name="user-list"),

    # Authentication
    path("auth/signup/", SignupAPIView.as_view(), name="signup"),
    path("auth/login/", LoginAPIView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutAPIView.as_view(), name="logout"),

    path(
        "profile/candidate/",
        CandidateProfileAPIView.as_view(),
        name="candidate-profile",
    ),

    path(
        "profile/employer/",
        EmployerProfileAPIView.as_view(),
        name="employer-profile",
    ),
    path(
        "profile/resume/upload/",
        ResumeUploadAPIView.as_view(),
        name="resume-upload",
    ),

    path(
        "profile/resume/",
        ResumeAPIView.as_view(),
        name="resume",
    ),
    path(
        "jobs/",
        JobListAPIView.as_view(),
        name="job-list",
    ),
    path(
        "jobs/featured/",
        FeaturedJobListAPIView.as_view(),
        name="featured-job-list",
    ),

    path(
        "jobs/latest/",
        LatestJobListAPIView.as_view(),
        name="latest-job-list",
    ),

    path(
        "jobs/",
        JobListAPIView.as_view(),
        name="job-list",
    ),
    path(
        "jobs/<int:job_id>/apply/",
        JobApplicationCreateAPIView.as_view(),
        name="job-application-create",
    ),
    path(
        "jobs/<int:pk>/",
        JobUpdateAPIView.as_view(),
        name="job-update",
    ),

    path(
        "jobs/<int:pk>/status/",
        JobStatusAPIView.as_view(),
        name="job-status",
    ),
    path(
        "applications/",
        ApplicationListAPIView.as_view(),
        name="application-list",
    ),

    path(
        "applications/<int:pk>/",
        ApplicationDetailAPIView.as_view(),
        name="application-detail",
    ),
    path(
        "applications/<int:pk>/status/",
        ApplicationStatusUpdateAPIView.as_view(),
        name="application-status-update",
    ),

    path(
        "applications/<int:pk>/history/",
        ApplicationStatusHistoryAPIView.as_view(),
        name="application-status-history",
    ),
]