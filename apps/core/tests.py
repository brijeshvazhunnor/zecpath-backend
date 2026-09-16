from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from apps.core.models import Job, Application

User = get_user_model()


class AuthenticationTests(APITestCase):
    """
    Tests for Zecpath authentication and role-based access control.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username="testadmin",
            email="testadmin@example.com",
            password="Admin@12345",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        self.employer = User.objects.create_user(
            username="testemployer",
            email="testemployer@example.com",
            password="Employer@12345",
            role="employer",
        )

        self.candidate = User.objects.create_user(
            username="testcandidate",
            email="testcandidate@example.com",
            password="Candidate@12345",
            role="candidate",
        )

    # ---------------------------------------------------------
    # SIGNUP TEST
    # ---------------------------------------------------------

    def test_candidate_signup(self):
        response = self.client.post(
            "/api/auth/signup/",
            {
                "username": "newcandidate",
                "email": "newcandidate@example.com",
                "password": "NewCandidate@12345",
                "phone": "9876543210",
                "role": "candidate",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(
                email="newcandidate@example.com"
            ).exists()
        )

    # ---------------------------------------------------------
    # LOGIN TEST
    # ---------------------------------------------------------

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "testadmin@example.com",
                "password": "Admin@12345",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    # ---------------------------------------------------------
    # INVALID LOGIN TEST
    # ---------------------------------------------------------

    def test_login_with_invalid_password(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "testadmin@example.com",
                "password": "WrongPassword@123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------------------------------------------------------
    # UNKNOWN USER TEST
    # ---------------------------------------------------------

    def test_login_with_unknown_email(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "unknown@example.com",
                "password": "Unknown@12345",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------------------------------------------------------
    # PROTECTED API - NO TOKEN
    # ---------------------------------------------------------

    def test_protected_endpoint_without_token(self):
        response = self.client.get("/api/users/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    # ---------------------------------------------------------
    # ADMIN ACCESS TEST
    # ---------------------------------------------------------

    def test_admin_can_access_users_endpoint(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ---------------------------------------------------------
    # CANDIDATE ACCESS DENIED
    # ---------------------------------------------------------

    def test_candidate_cannot_access_admin_users_endpoint(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.get("/api/users/")

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    # ---------------------------------------------------------
    # EMPLOYER ACCESS DENIED
    # ---------------------------------------------------------

    def test_employer_cannot_access_admin_users_endpoint(self):
        self.client.force_authenticate(user=self.employer)

        response = self.client.get("/api/users/")

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    # ---------------------------------------------------------
    # REFRESH TOKEN TEST
    # ---------------------------------------------------------

    def test_refresh_token(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "email": "testadmin@example.com",
                "password": "Admin@12345",
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK
        )

        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            "/api/auth/refresh/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn("access", response.data)




class ApplicationSecurityTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="appadmin",
            email="appadmin@example.com",
            password="Admin@12345",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        self.employer1 = User.objects.create_user(
            username="employer1",
            email="employer1@example.com",
            password="Employer@12345",
            role="employer",
        )

        self.employer2 = User.objects.create_user(
            username="employer2",
            email="employer2@example.com",
            password="Employer@12345",
            role="employer",
        )

        self.candidate1 = User.objects.create_user(
            username="candidate1",
            email="candidate1@example.com",
            password="Candidate@12345",
            role="candidate",
        )

        self.candidate2 = User.objects.create_user(
            username="candidate2",
            email="candidate2@example.com",
            password="Candidate@12345",
            role="candidate",
        )

        self.job1 = Job.objects.create(
            employer=self.employer1.employer,
            title="Python Developer",
            description="Python backend development",
            location="Kochi",
            required_skills="Python, Django",
            experience="0-2 years",
        )

        self.job2 = Job.objects.create(
            employer=self.employer2.employer,
            title="ML Engineer",
            description="Machine learning development",
            location="Bangalore",
            required_skills="Python, ML",
            experience="1-3 years",
        )

        self.application1 = Application.objects.create(
            job=self.job1,
            candidate=self.candidate1.candidate,
            status="applied",
        )

        self.application2 = Application.objects.create(
            job=self.job2,
            candidate=self.candidate2.candidate,
            status="shortlisted",
        )

    def test_candidate_sees_only_own_applications(self):
        self.client.force_authenticate(
            user=self.candidate1
        )

        response = self.client.get(
            "/api/applications/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["count"],
            1
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            self.application1.id
        )

    def test_employer_sees_only_own_job_applications(self):
        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.get(
            "/api/applications/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["count"],
            1
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            self.application1.id
        )

    def test_admin_can_see_all_applications(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            "/api/applications/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["count"],
            2
        )