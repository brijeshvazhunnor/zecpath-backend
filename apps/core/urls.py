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
    EmployerJobListAPIView,
    EmployerJobUpdateAPIView,
    EmployerJobCloseAPIView,
    EmployerApplicantListAPIView,
    EmployerAnalyticsAPIView,
    CandidateApplicationListAPIView,
    CandidateApplicationDetailAPIView,
    CandidateInterviewListAPIView,
    CandidateSavedJobListCreateAPIView,
    CandidateSavedJobDeleteAPIView,
    CandidateApplicationTimelineAPIView,
    CandidateRecommendationAPIView,
    AdminEmployerApprovalAPIView,
    AdminUserBlockAPIView,
    AdminUserUnblockAPIView,
    AdminFlagAccountAPIView,
    AdminJobManageAPIView,
    AdminRemoveSpamJobAPIView,
    AdminPlatformStatsAPIView,
    AdminUserGrowthAPIView,
    AdminJobActivityAPIView,
    AdminAuditLogListAPIView,
    ResumeTextExtractionAPIView,
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
    path(
        "employer/jobs/",
        EmployerJobListAPIView.as_view(),
        name="employer-job-list",
    ),

    path(
        "employer/jobs/<int:pk>/",
        EmployerJobUpdateAPIView.as_view(),
        name="employer-job-update",
    ),

    path(
        "employer/jobs/<int:pk>/close/",
        EmployerJobCloseAPIView.as_view(),
        name="employer-job-close",
    ),
    path(
        "employer/applicants/",
        EmployerApplicantListAPIView.as_view(),
        name="employer-applicant-list",
    ),
    path(
        "employer/analytics/",
        EmployerAnalyticsAPIView.as_view(),
        name="employer-analytics",
    ),
        # Candidate Dashboard
    path(
        "candidate/applications/",
        CandidateApplicationListAPIView.as_view(),
        name="candidate-application-list",
    ),

    path(
        "candidate/applications/<int:pk>/",
        CandidateApplicationDetailAPIView.as_view(),
        name="candidate-application-detail",
    ),

    path(
        "candidate/applications/<int:pk>/timeline/",
        CandidateApplicationTimelineAPIView.as_view(),
        name="candidate-application-timeline",
    ),

    path(
        "candidate/interviews/",
        CandidateInterviewListAPIView.as_view(),
        name="candidate-interview-list",
    ),

    path(
        "candidate/saved-jobs/",
        CandidateSavedJobListCreateAPIView.as_view(),
        name="candidate-saved-job-list-create",
    ),

    path(
        "candidate/saved-jobs/<int:job_id>/",
        CandidateSavedJobDeleteAPIView.as_view(),
        name="candidate-saved-job-delete",
    ),
    path(
        "candidate/recommendations/",
        CandidateRecommendationAPIView.as_view(),
        name="candidate-recommendations",
    ),
    # =========================================================
    # ADMIN CONTROL PANEL
    # =========================================================

    path(
        "admin/employers/<int:pk>/approve/",
        AdminEmployerApprovalAPIView.as_view(),
        name="admin-employer-approve",
    ),

    path(
        "admin/users/<int:pk>/block/",
        AdminUserBlockAPIView.as_view(),
        name="admin-user-block",
    ),

    path(
        "admin/users/<int:pk>/unblock/",
        AdminUserUnblockAPIView.as_view(),
        name="admin-user-unblock",
    ),

    path(
        "admin/users/<int:pk>/flag/",
        AdminFlagAccountAPIView.as_view(),
        name="admin-user-flag",
    ),

    path(
        "admin/jobs/<int:pk>/manage/",
        AdminJobManageAPIView.as_view(),
        name="admin-job-manage",
    ),

    path(
        "admin/jobs/<int:pk>/remove-spam/",
        AdminRemoveSpamJobAPIView.as_view(),
        name="admin-job-remove-spam",
    ),

    # =========================================================
    # ADMIN MONITORING
    # =========================================================

    path(
        "admin/monitoring/stats/",
        AdminPlatformStatsAPIView.as_view(),
        name="admin-platform-stats",
    ),

    path(
        "admin/monitoring/user-growth/",
        AdminUserGrowthAPIView.as_view(),
        name="admin-user-growth",
    ),

    path(
        "admin/monitoring/job-activity/",
        AdminJobActivityAPIView.as_view(),
        name="admin-job-activity",
    ),

    # =========================================================
    # ADMIN AUDIT LOGS
    # =========================================================

    path(
        "admin/audit-logs/",
        AdminAuditLogListAPIView.as_view(),
        name="admin-audit-logs",
    ),
    path(
        "resume/parse/",
        ResumeTextExtractionAPIView.as_view(),
        name="resume-parse",
    ),

]