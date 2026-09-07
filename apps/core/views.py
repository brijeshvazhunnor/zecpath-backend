from django.http import JsonResponse
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Job
from .serializers import UserSerializer, JobSerializer

def home(request):
    return JsonResponse({
        "message": "Hello Zecpath Backend"
    })


class JobListAPIView(APIView):

    def get(self, request):
        jobs = Job.objects.all()

        serializer = JobSerializer(jobs, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class JobCreateAPIView(APIView):

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

    def get(self, request):
        users = User.objects.all()

        serializer = UserSerializer(users, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )