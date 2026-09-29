from django.http import JsonResponse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)
from rest_framework.parsers import (
    MultiPartParser,
    FormParser,
)

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework_simplejwt.exceptions import (
    TokenError,
)

from .models import (
    User,
    Job,
    Candidate,
    Employer,
    Resume,
    Application,
    ApplicationStatusHistory,
    SavedJob,
)

from .serializers import (
    UserSerializer,
    JobSerializer,
    CandidateProfileSerializer,
    EmployerProfileSerializer,
    ResumeSerializer,
    ApplicationSerializer,
    ApplicationStatusHistorySerializer,
    EmployerApplicantSerializer,
    SavedJobSerializer,
    CandidateApplicationSerializer,
    CandidateApplicationTimelineSerializer,
    CandidateRecommendationSerializer,
)

from .auth_serializers import (
    SignupSerializer,
    EmailTokenObtainPairSerializer,
)

from .permissions.roles import (
    IsAdmin,
    IsAdminOrEmployer,
    IsCandidate,
    IsEmployer,
)

from .permissions.profile_permissions import (
    IsCandidateProfileOwner,
    IsEmployerProfileOwner,
)


# =========================================================
# HOME
# =========================================================

def home(request):
    return JsonResponse({
        "message": "Hello Zecpath Backend"
    })


# =========================================================
# JOB LIST - PAGINATION, FILTERING & SEARCH
# =========================================================
# =========================================================
# FEATURED JOBS
# =========================================================

class FeaturedJobListAPIView(ListAPIView):

    serializer_class = JobSerializer

    permission_classes = [
        AllowAny
    ]

    def get_queryset(self):

        return Job.objects.filter(
            status=Job.Status.ACTIVE,
            featured=True
        ).select_related(
            "employer"
        ).order_by(
            "-created_at"
        )


# =========================================================
# LATEST JOBS
# =========================================================

class LatestJobListAPIView(ListAPIView):

    serializer_class = JobSerializer

    permission_classes = [
        AllowAny
    ]

    def get_queryset(self):

        return Job.objects.filter(
            status=Job.Status.ACTIVE
        ).select_related(
            "employer"
        ).order_by(
            "-created_at"
        )
# =========================================================
# PUBLIC JOB LIST - FILTERING, SEARCH & PAGINATION
# =========================================================

class JobListAPIView(ListAPIView):

    serializer_class = JobSerializer

    # Public job discovery API
    permission_classes = [
        AllowAny
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    # Exact/basic filters
    filterset_fields = [
        "location",
        "job_type",
        "status",
    ]

    # Keyword search
    search_fields = [
        "title",
        "description",
        "required_skills",
        "location",
        "experience",
    ]

    # Ordering
    ordering_fields = [
        "created_at",
        "title",
        "experience",
        "salary_min",
        "salary_max",
    ]

    ordering = [
        "-created_at"
    ]

    def get_queryset(self):

        # -------------------------------------------------
        # Only active jobs are publicly visible
        # -------------------------------------------------

        queryset = Job.objects.filter(
            status=Job.Status.ACTIVE
        ).select_related(
            "employer"
        )

        # -------------------------------------------------
        # Skill-based filtering
        # Example:
        # /api/jobs/?skills=python
        # -------------------------------------------------

        skills = self.request.query_params.get("skills")

        if skills:
            queryset = queryset.filter(
                required_skills__icontains=skills
            )

        # -------------------------------------------------
        # Experience filtering
        # Example:
        # /api/jobs/?experience=2 years
        # -------------------------------------------------

        experience = self.request.query_params.get("experience")

        if experience:
            queryset = queryset.filter(
                experience__icontains=experience
            )

        # -------------------------------------------------
        # Salary range filtering
        #
        # Example:
        # /api/jobs/?salary_min=30000
        # /api/jobs/?salary_max=60000
        #
        # Jobs whose salary range overlaps the requested
        # candidate salary range are returned.
        # -------------------------------------------------

        salary_min = self.request.query_params.get(
            "salary_min"
        )

        salary_max = self.request.query_params.get(
            "salary_max"
        )

        if salary_min:
            try:
                salary_min = float(salary_min)

                queryset = queryset.filter(
                    salary_max__gte=salary_min
                )

            except ValueError:
                pass

        if salary_max:
            try:
                salary_max = float(salary_max)

                queryset = queryset.filter(
                    salary_min__lte=salary_max
                )

            except ValueError:
                pass

        # -------------------------------------------------
        # Location filtering
        # Example:
        # /api/jobs/?location=Kochi
        # -------------------------------------------------

        location = self.request.query_params.get(
            "location"
        )

        if location:
            queryset = queryset.filter(
                location__icontains=location
            )

        # -------------------------------------------------
        # Job type filtering
        # Example:
        # /api/jobs/?job_type=full_time
        # -------------------------------------------------

        job_type = self.request.query_params.get(
            "job_type"
        )

        if job_type:
            queryset = queryset.filter(
                job_type=job_type
            )

        # -------------------------------------------------
        # Created date filtering
        # -------------------------------------------------

        created_after = self.request.query_params.get(
            "created_after"
        )

        created_before = self.request.query_params.get(
            "created_before"
        )

        if created_after:
            queryset = queryset.filter(
                created_at__date__gte=created_after
            )

        if created_before:
            queryset = queryset.filter(
                created_at__date__lte=created_before
            )

        return queryset


# =========================================================
# JOB CREATE
# =========================================================

class JobCreateAPIView(APIView):

    permission_classes = [
        IsEmployer
    ]

    def post(self, request):

        serializer = JobSerializer(
            data=request.data
        )

        if serializer.is_valid():

            job = serializer.save(
                employer=request.user.employer
            )

            return Response(
                JobSerializer(job).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# JOB UPDATE
# =========================================================

class JobUpdateAPIView(RetrieveUpdateAPIView):

    serializer_class = JobSerializer

    permission_classes = [
        IsEmployer
    ]

    def get_queryset(self):

        return Job.objects.filter(
            employer__user=self.request.user
        ).select_related(
            "employer"
        )


# =========================================================
# JOB ACTIVATE / DEACTIVATE
# =========================================================

class JobStatusAPIView(APIView):

    permission_classes = [
        IsEmployer
    ]

    def patch(self, request, pk):

        try:
            job = Job.objects.get(
                pk=pk,
                employer__user=request.user
            )

        except Job.DoesNotExist:

            return Response(
                {
                    "error": "Job not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get("status")

        if new_status not in [
            Job.Status.ACTIVE,
            Job.Status.INACTIVE,
        ]:

            return Response(
                {
                    "error": (
                        "Status must be either "
                        "'active' or 'inactive'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        job.status = new_status
        job.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "message": "Job status updated successfully.",
                "job_id": job.id,
                "status": job.status,
            },
            status=status.HTTP_200_OK
        )

class EmployerJobListAPIView(ListAPIView):

    serializer_class = JobSerializer
    permission_classes = [
        IsEmployer
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = [
        "status",
        "job_type",
        "location",
    ]

    search_fields = [
        "title",
        "description",
        "required_skills",
        "location",
    ]

    ordering_fields = [
        "created_at",
        "title",
        "experience",
        "salary_min",
        "salary_max",
    ]

    ordering = [
        "-created_at"
    ]

    def get_queryset(self):

        return Job.objects.filter(
            employer__user=self.request.user
        ).select_related(
            "employer"
        )


class EmployerJobUpdateAPIView(RetrieveUpdateAPIView):

    serializer_class = JobSerializer
    permission_classes = [
        IsEmployer
    ]

    def get_queryset(self):

        return Job.objects.filter(
            employer__user=self.request.user
        ).select_related(
            "employer"
        )


class EmployerJobCloseAPIView(APIView):

    permission_classes = [
        IsEmployer
    ]

    def patch(self, request, pk):

        try:
            job = Job.objects.get(
                pk=pk,
                employer__user=request.user,
            )

        except Job.DoesNotExist:

            return Response(
                {
                    "error": "Job not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if job.status == Job.Status.INACTIVE:

            return Response(
                {
                    "error": "Job is already closed."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        job.status = Job.Status.INACTIVE

        job.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            {
                "message": "Job closed successfully.",
                "job_id": job.id,
                "status": job.status,
            },
            status=status.HTTP_200_OK
        )
# =========================================================
# APPLY FOR JOB
# =========================================================

class JobApplicationCreateAPIView(APIView):

    permission_classes = [
        IsCandidate
    ]

    def post(self, request, job_id):

        # -------------------------------------------------
        # Get the candidate profile
        # -------------------------------------------------

        candidate = request.user.candidate

        # -------------------------------------------------
        # Check whether the job exists and is active
        # -------------------------------------------------

        try:
            job = Job.objects.get(
                pk=job_id,
                status=Job.Status.ACTIVE
            )
        except Job.DoesNotExist:
            return Response(
                {
                    "error": "Job not found or is not currently active."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # -------------------------------------------------
        # Prevent duplicate applications
        # -------------------------------------------------

        if Application.objects.filter(
            candidate=candidate,
            job=job
        ).exists():

            return Response(
                {
                    "error": "You have already applied for this job."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # -------------------------------------------------
        # Candidate must have an active resume
        # -------------------------------------------------

        try:
            resume = candidate.resume
        except Resume.DoesNotExist:
            return Response(
                {
                    "error": "Please upload a resume before applying."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not resume.is_active:
            return Response(
                {
                    "error": "Please upload or activate a resume before applying."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # -------------------------------------------------
        # Create resume snapshot
        # -------------------------------------------------

        resume_snapshot = {
            "original_filename": resume.original_filename,
            "file_size": resume.file_size,
            "uploaded_at": resume.uploaded_at.isoformat(),
        }

        # -------------------------------------------------
        # Create application
        # -------------------------------------------------

        application = Application.objects.create(
            job=job,
            candidate=candidate,
            resume_snapshot=resume_snapshot,
            status="applied"
        )

        return Response(
            ApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )

# =========================================================
# USERS - PAGINATION, FILTERING & SEARCH
# =========================================================

class UserTestAPIView(ListAPIView):

    serializer_class = UserSerializer

    permission_classes = [
        IsAdmin
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = [
        "role",
        "is_active",
        "is_verified",
    ]

    search_fields = [
        "username",
        "email",
        "phone",
    ]

    ordering_fields = [
        "created_at",
        "username",
        "email",
    ]

    ordering = [
        "-created_at"
    ]

    def get_queryset(self):

        return User.objects.select_related(
            "candidate",
            "employer",
        )


# =========================================================
# SIGNUP
# =========================================================

class SignupAPIView(APIView):

    permission_classes = [
        AllowAny
    ]

    def post(self, request):

        serializer = SignupSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.save()

            return Response(
                {
                    "message": "User registered successfully",
                    "user_id": user.id,
                    "email": user.email,
                    "role": user.role,
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# LOGIN
# =========================================================

class LoginAPIView(TokenObtainPairView):

    permission_classes = [
        AllowAny
    ]

    serializer_class = (
        EmailTokenObtainPairSerializer
    )


# =========================================================
# LOGOUT
# =========================================================

class LogoutAPIView(APIView):

    def post(self, request):

        try:

            refresh_token = request.data["refresh"]

            token = RefreshToken(
                refresh_token
            )

            token.blacklist()

            return Response(
                {
                    "message": "Logout successful"
                },
                status=status.HTTP_205_RESET_CONTENT
            )

        except (KeyError, TokenError):

            return Response(
                {
                    "error":
                    "Invalid or expired refresh token"
                },
                status=status.HTTP_400_BAD_REQUEST
            )


# =========================================================
# CANDIDATE PROFILE
# =========================================================

class CandidateProfileAPIView(
    RetrieveUpdateDestroyAPIView
):

    serializer_class = CandidateProfileSerializer

    permission_classes = [
        IsAuthenticated,
        IsCandidateProfileOwner,
    ]

    def get_object(self):

        return Candidate.objects.get(
            user=self.request.user
        )

    def perform_destroy(self, instance):

        instance.is_active = False

        instance.save(
            update_fields=[
                "is_active"
            ]
        )


# =========================================================
# EMPLOYER PROFILE
# =========================================================

class EmployerProfileAPIView(
    RetrieveUpdateDestroyAPIView
):

    serializer_class = EmployerProfileSerializer

    permission_classes = [
        IsAuthenticated,
        IsEmployerProfileOwner,
    ]

    def get_object(self):

        return Employer.objects.get(
            user=self.request.user
        )

    def perform_destroy(self, instance):

        instance.is_active = False

        instance.save(
            update_fields=[
                "is_active"
            ]
        )


# =========================================================
# RESUME UPLOAD
# =========================================================

class ResumeUploadAPIView(APIView):

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    permission_classes = [
        IsAuthenticated,
        IsCandidateProfileOwner,
    ]

    def post(self, request):

        try:

            candidate = Candidate.objects.get(
                user=request.user
            )

        except Candidate.DoesNotExist:

            return Response(
                {
                    "error":
                    "Candidate profile not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        resume = Resume.objects.filter(
            candidate=candidate
        ).first()

        serializer = ResumeSerializer(
            instance=resume,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            uploaded_file = request.FILES.get(
                "file"
            )

            if uploaded_file:

                serializer.save(
                    candidate=candidate,
                    original_filename=uploaded_file.name,
                    file_size=uploaded_file.size
                )

            return Response(
                serializer.data,
                status=(
                    status.HTTP_200_OK
                    if resume
                    else status.HTTP_201_CREATED
                )
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# RESUME
# =========================================================

class ResumeAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsCandidateProfileOwner,
    ]

    def get(self, request):

        try:

            candidate = Candidate.objects.get(
                user=request.user
            )

            resume = Resume.objects.get(
                candidate=candidate
            )

        except (
            Candidate.DoesNotExist,
            Resume.DoesNotExist
        ):

            return Response(
                {
                    "error":
                    "Resume not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ResumeSerializer(
            resume
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def delete(self, request):

        try:

            candidate = Candidate.objects.get(
                user=request.user
            )

            resume = Resume.objects.get(
                candidate=candidate
            )

        except (
            Candidate.DoesNotExist,
            Resume.DoesNotExist
        ):

            return Response(
                {
                    "error":
                    "Resume not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        resume.is_active = False

        resume.save(
            update_fields=[
                "is_active"
            ]
        )

        return Response(
            {
                "message":
                "Resume deactivated successfully."
            },
            status=status.HTTP_204_NO_CONTENT
        )

# =========================================================
# APPLICATIONS - PAGINATION, FILTERING & SEARCH
# =========================================================

class ApplicationListAPIView(ListAPIView):

    serializer_class = ApplicationSerializer

    permission_classes = [
        IsAuthenticated
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = [
        "status",
        "job",
        "candidate",
    ]

    search_fields = [
        "job__title",
        "job__description",
        "candidate__full_name",
        "candidate__skills",
    ]

    ordering_fields = [
        "applied_at",
        "status",
    ]

    ordering = [
        "-applied_at"
    ]

    def get_queryset(self):

        user = self.request.user

        queryset = Application.objects.select_related(
            "job",
            "candidate",
        )

        # Admin can view all applications
        if user.role == User.Role.ADMIN:
            return queryset

        # Candidate can view only their own applications
        if user.role == User.Role.CANDIDATE:
            return queryset.filter(
                candidate__user=user
            )

        # Employer can view applications only
        # for jobs belonging to their company
        if user.role == User.Role.EMPLOYER:
            return queryset.filter(
                job__employer__user=user
            )

        # Unknown/unrecognized roles get no data
        return queryset.none()


# =========================================================
# APPLICATION DETAIL / TRACKING
# =========================================================

class ApplicationDetailAPIView(RetrieveAPIView):

    serializer_class = ApplicationSerializer
    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        user = self.request.user

        queryset = Application.objects.select_related(
            "job",
            "candidate",
        )

        # Admin can view all applications
        if user.role == User.Role.ADMIN:
            return queryset

        # Candidate can view only their own applications
        if user.role == User.Role.CANDIDATE:
            return queryset.filter(
                candidate__user=user
            )

        # Employer can view applications
        # for jobs belonging to their company
        if user.role == User.Role.EMPLOYER:
            return queryset.filter(
                job__employer__user=user
            )

        return queryset.none()


class ApplicationStatusUpdateAPIView(APIView):

    permission_classes = [
        IsEmployer
    ]

    def patch(self, request, pk):

        new_status = request.data.get("status")

        valid_statuses = [
            choice[0]
            for choice in Application.STATUS_CHOICES
        ]

        if new_status not in valid_statuses:
            return Response(
                {
                    "error": "Invalid application status.",
                    "allowed_statuses": valid_statuses,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            application = Application.objects.select_related(
                "job",
                "job__employer",
                "candidate",
            ).get(
                pk=pk,
                job__employer__user=request.user,
            )

        except Application.DoesNotExist:
            return Response(
                {
                    "error": "Application not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        old_status = application.status

        if old_status == new_status:
            return Response(
                {
                    "error": "Application is already in this status."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not application.can_transition_to(new_status):
            return Response(
                {
                    "error": (
                        f"Invalid status transition: "
                        f"{old_status} -> {new_status}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        application.status = new_status
        application.save(
            update_fields=[
                "status",
            ]
        )

        ApplicationStatusHistory.objects.create(
            application=application,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            action=f"Status changed from {old_status} to {new_status}",
        )

        return Response(
            {
                "message": "Application status updated successfully.",
                "application_id": application.id,
                "old_status": old_status,
                "new_status": new_status,
            },
            status=status.HTTP_200_OK
        )

class ApplicationStatusHistoryAPIView(ListAPIView):

    serializer_class = ApplicationStatusHistorySerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        user = self.request.user

        queryset = ApplicationStatusHistory.objects.select_related(
            "application",
            "changed_by",
        ).filter(
            application_id=self.kwargs["pk"]
        )

        if user.role == User.Role.ADMIN:
            return queryset

        if user.role == User.Role.CANDIDATE:
            return queryset.filter(
                application__candidate__user=user
            )

        if user.role == User.Role.EMPLOYER:
            return queryset.filter(
                application__job__employer__user=user
            )

        return queryset.none()


class EmployerApplicantListAPIView(ListAPIView):

    serializer_class = EmployerApplicantSerializer

    permission_classes = [
        IsEmployer
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = [
        "status",
        "job",
    ]

    search_fields = [
        "candidate__full_name",
        "candidate__email",
        "candidate__skills",
        "candidate__education",
        "candidate__experience",
        "job__title",
    ]

    ordering_fields = [
        "applied_at",
        "status",
    ]

    ordering = [
        "-applied_at"
    ]

    def get_queryset(self):

        return Application.objects.filter(
            job__employer__user=self.request.user
        ).select_related(
            "job",
            "candidate",
        )

class EmployerAnalyticsAPIView(APIView):

    permission_classes = [
        IsEmployer
    ]

    def get(self, request):

        employer = request.user.employer

        jobs = Job.objects.filter(
            employer=employer
        )

        applications = Application.objects.filter(
            job__employer=employer
        )

        total_jobs = jobs.count()

        active_jobs = jobs.filter(
            status=Job.Status.ACTIVE
        ).count()

        closed_jobs = jobs.filter(
            status=Job.Status.INACTIVE
        ).count()

        total_applications = applications.count()

        shortlisted_applications = applications.filter(
            status="shortlisted"
        ).count()

        interview_scheduled = applications.filter(
            status="interview_scheduled"
        ).count()

        selected_applications = applications.filter(
            status="selected"
        ).count()

        rejected_applications = applications.filter(
            status="rejected"
        ).count()

        if total_applications > 0:
            shortlist_ratio = round(
                (
                    shortlisted_applications
                    / total_applications
                ) * 100,
                2
            )
        else:
            shortlist_ratio = 0

        return Response(
            {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "closed_jobs": closed_jobs,
                "total_applications": total_applications,
                "shortlisted_applications": shortlisted_applications,
                "interview_scheduled": interview_scheduled,
                "selected_applications": selected_applications,
                "rejected_applications": rejected_applications,
                "shortlist_ratio": shortlist_ratio,
            },
            status=status.HTTP_200_OK
        )

# =========================================================
# CANDIDATE DASHBOARD - APPLICATIONS
# =========================================================

class CandidateApplicationListAPIView(ListAPIView):

    serializer_class = CandidateApplicationSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):

        return Application.objects.filter(
            candidate__user=self.request.user
        ).select_related(
            "job",
            "job__employer",
            "candidate",
        ).order_by(
            "-applied_at"
        )

# =========================================================
# CANDIDATE APPLICATION DETAIL
# =========================================================

class CandidateApplicationDetailAPIView(RetrieveAPIView):

    serializer_class = CandidateApplicationSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):

        return Application.objects.filter(
            candidate__user=self.request.user
        ).select_related(
            "job",
            "job__employer",
            "candidate",
        )

# =========================================================
# CANDIDATE INTERVIEW STATUS
# =========================================================

class CandidateInterviewListAPIView(ListAPIView):

    serializer_class = CandidateApplicationSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):

        return Application.objects.filter(
            candidate__user=self.request.user,
            status="interview_scheduled",
        ).select_related(
            "job",
            "job__employer",
            "candidate",
        ).order_by(
            "-applied_at"
        )

# =========================================================
# CANDIDATE SAVED JOBS
# =========================================================

class CandidateSavedJobListCreateAPIView(APIView):

    permission_classes = [IsCandidate]

    def get(self, request):

        saved_jobs = SavedJob.objects.filter(
            candidate=request.user.candidate
        ).select_related(
            "job",
            "job__employer",
        )

        serializer = SavedJobSerializer(
            saved_jobs,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):

        job_id = request.data.get("job")

        if not job_id:
            return Response(
                {"error": "Job ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            job = Job.objects.select_related(
                "employer"
            ).get(
                id=job_id,
                status=Job.Status.ACTIVE,
            )
        except Job.DoesNotExist:
            return Response(
                {"error": "Active job not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if SavedJob.objects.filter(
            candidate=request.user.candidate,
            job=job,
        ).exists():
            return Response(
                {"error": "Job is already saved."},
                status=status.HTTP_400_BAD_REQUEST
            )

        saved_job = SavedJob.objects.create(
            candidate=request.user.candidate,
            job=job,
        )

        serializer = SavedJobSerializer(saved_job)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

class CandidateSavedJobDeleteAPIView(APIView):

    permission_classes = [IsCandidate]

    def delete(self, request, job_id):

        try:
            saved_job = SavedJob.objects.get(
                candidate=request.user.candidate,
                job_id=job_id,
            )
        except SavedJob.DoesNotExist:
            return Response(
                {"error": "Saved job not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        saved_job.delete()

        return Response(
            {"message": "Job removed from saved jobs."},
            status=status.HTTP_204_NO_CONTENT
        )

# =========================================================
# CANDIDATE APPLICATION TIMELINE
# =========================================================

class CandidateApplicationTimelineAPIView(ListAPIView):

    serializer_class = CandidateApplicationTimelineSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):

        return ApplicationStatusHistory.objects.filter(
            application__id=self.kwargs["pk"],
            application__candidate__user=self.request.user,
        ).order_by(
            "changed_at"
        )

class CandidateRecommendationAPIView(ListAPIView):
    serializer_class = CandidateRecommendationSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        candidate = self.request.user.candidate

        candidate_skills = {
            skill.strip().lower()
            for skill in candidate.skills.replace(";", ",").replace("\n", ",").split(",")
            if skill.strip()
        }

        jobs = Job.objects.filter(
            status=Job.Status.ACTIVE
        ).select_related("employer")

        applied_job_ids = Application.objects.filter(
            candidate=candidate
        ).values_list("job_id", flat=True)

        jobs = jobs.exclude(id__in=applied_job_ids)

        recommendations = []

        for job in jobs:
            required_skills = {
                skill.strip().lower()
                for skill in job.required_skills.replace(";", ",").replace("\n", ",").split(",")
                if skill.strip()
            }

            if not required_skills:
                continue

            matched_skills = sorted(
                candidate_skills.intersection(required_skills)
            )

            match_score = round(
                (len(matched_skills) / len(required_skills)) * 100,
                2
            )

            job.match_score = match_score
            job.matched_skills = matched_skills

            recommendations.append(job)

        recommendations.sort(
            key=lambda job: (
                job.match_score,
                job.created_at
            ),
            reverse=True
        )

        return recommendations