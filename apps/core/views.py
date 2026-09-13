from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User, Job
from .serializers import UserSerializer, JobSerializer
from .permissions.roles import IsAdmin, IsAdminOrEmployer, IsCandidate
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .auth_serializers import (
    SignupSerializer,
    EmailTokenObtainPairSerializer,
)

from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Candidate, Employer
from .serializers import (
    CandidateProfileSerializer,
    EmployerProfileSerializer,
)

from .permissions.profile_permissions import (
    IsCandidateProfileOwner,
    IsEmployerProfileOwner,
)


def home(request):
    return JsonResponse({
        "message": "Hello Zecpath Backend"
    })


class JobListAPIView(APIView):

    def get(self, request):
        jobs = Job.objects.all()

        serializer = JobSerializer(
            jobs,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class JobCreateAPIView(APIView):
    permission_classes = [IsAdminOrEmployer]

    def post(self, request):
        serializer = JobSerializer(data=request.data)

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


class UserTestAPIView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class SignupAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = SignupSerializer(data=request.data)

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

class LoginAPIView(TokenObtainPairView):

    permission_classes = [AllowAny]

    serializer_class = EmailTokenObtainPairSerializer


from rest_framework_simplejwt.views import TokenRefreshView


class LogoutAPIView(APIView):

    def post(self, request):

        try:

            refresh_token = request.data["refresh"]

            token = RefreshToken(refresh_token)

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
                    "error": "Invalid or expired refresh token"
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class CandidateProfileAPIView(RetrieveUpdateDestroyAPIView):

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
            update_fields=["is_active"]
        )


class EmployerProfileAPIView(RetrieveUpdateDestroyAPIView):

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
            update_fields=["is_active"]
        )


from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import RetrieveUpdateAPIView

from .models import Resume, Candidate
from .serializers import ResumeSerializer

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
                {"error": "Candidate profile not found."},
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

            uploaded_file = request.FILES.get("file")

            if uploaded_file:

                serializer.save(
                    candidate=candidate,
                    original_filename=uploaded_file.name,
                    file_size=uploaded_file.size
                )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
                if resume
                else status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


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
                {"error": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ResumeSerializer(resume)

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
                {"error": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        resume.is_active = False
        resume.save(update_fields=["is_active"])

        return Response(
            {"message": "Resume deactivated successfully."},
            status=status.HTTP_204_NO_CONTENT
        )