from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User, Job
from .serializers import UserSerializer, JobSerializer

from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .auth_serializers import (
    SignupSerializer,
    EmailTokenObtainPairSerializer,
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


class UserTestAPIView(APIView):

    def get(self, request):

        users = User.objects.all()

        serializer = UserSerializer(
            users,
            many=True
        )

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