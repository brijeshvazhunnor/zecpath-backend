from django.http import JsonResponse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView,
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

from .models import (
    User,
    Job,
    Candidate,
    Employer,
    Resume,
    Application,
)

from .serializers import (
    UserSerializer,
    JobSerializer,
    CandidateProfileSerializer,
    EmployerProfileSerializer,
    ResumeSerializer,
    ApplicationSerializer,
)

from .auth_serializers import (
    SignupSerializer,
    EmailTokenObtainPairSerializer,
)

from .permissions.roles import (
    IsAdmin,
    IsAdminOrEmployer,
    IsCandidate,
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

class JobListAPIView(ListAPIView):

    serializer_class = JobSerializer

    permission_classes = [
        IsAuthenticated
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = [
        "location",
        "experience",
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
    ]

    ordering = [
        "-created_at"
    ]

    def get_queryset(self):

        queryset = Job.objects.select_related(
            "employer"
        )

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
        IsAdminOrEmployer
    ]

    def post(self, request):

        serializer = JobSerializer(
            data=request.data
        )

        if serializer.is_valid():

            job = serializer.save()

            return Response(
                JobSerializer(job).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
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

        except Exception:

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

        queryset = Application.objects.select_related(
            "job",
            "candidate",
        )

        applied_after = self.request.query_params.get(
            "applied_after"
        )

        applied_before = self.request.query_params.get(
            "applied_before"
        )

        if applied_after:
            queryset = queryset.filter(
                applied_at__date__gte=applied_after
            )

        if applied_before:
            queryset = queryset.filter(
                applied_at__date__lte=applied_before
            )

        return queryset