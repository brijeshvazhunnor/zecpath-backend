from django.urls import path

from .views import (
    JobListAPIView,
    JobCreateAPIView,
    UserTestAPIView,
    SignupAPIView,
    LoginAPIView,
    LogoutAPIView,
    CandidateProfileAPIView,
    EmployerProfileAPIView,
)

from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    # Existing APIs
    path("jobs/", JobListAPIView.as_view(), name="job-list"),
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
]