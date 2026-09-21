from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from apps.core.models import (
    Job,
    Application,
    Resume,
    ApplicationStatusHistory,
)
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


    # =========================================================
    # DAY 18 - JOB APPLICATION TESTS
    # =========================================================

    def test_candidate_can_apply_for_active_job(self):
        resume = Resume.objects.create(
            candidate=self.candidate1.candidate,
            original_filename="candidate1_resume.pdf",
            file_size=1024,
            is_active=True,
        )

        self.client.force_authenticate(
            user=self.candidate1
        )

        response = self.client.post(
            f"/api/jobs/{self.job2.id}/apply/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            Application.objects.filter(
                candidate=self.candidate1.candidate,
                job=self.job2
            ).exists()
        )

        application = Application.objects.get(
            candidate=self.candidate1.candidate,
            job=self.job2
        )

        self.assertEqual(
            application.status,
            "applied"
        )

        self.assertEqual(
            application.resume_snapshot["original_filename"],
            "candidate1_resume.pdf"
        )

    def test_duplicate_application_is_rejected(self):
        resume = Resume.objects.create(
            candidate=self.candidate1.candidate,
            original_filename="candidate1_resume.pdf",
            file_size=1024,
            is_active=True,
        )

        self.client.force_authenticate(
            user=self.candidate1
        )

        response = self.client.post(
            f"/api/jobs/{self.job2.id}/apply/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        response = self.client.post(
            f"/api/jobs/{self.job2.id}/apply/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            Application.objects.filter(
                candidate=self.candidate1.candidate,
                job=self.job2
            ).count(),
            1
        )

    def test_employer_cannot_apply_for_job(self):
        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.post(
            f"/api/jobs/{self.job2.id}/apply/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_candidate_without_resume_cannot_apply(self):
        self.client.force_authenticate(
            user=self.candidate1
        )

        response = self.client.post(
            f"/api/jobs/{self.job2.id}/apply/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "resume",
            str(response.data).lower()
        )

    def test_candidate_cannot_apply_for_inactive_job(self):
        self.job2.status = Job.Status.INACTIVE
        self.job2.save(update_fields=["status"])

        resume = Resume.objects.create(
            candidate=self.candidate1.candidate,
            original_filename="candidate1_resume.pdf",
            file_size=1024,
            is_active=True,
        )

        self.client.force_authenticate(
            user=self.candidate1
        )

        response = self.client.post(
            f"/api/jobs/{self.job2.id}/apply/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_candidate_can_view_own_application_detail(self):
        self.client.force_authenticate(
            user=self.candidate1
        )

        response = self.client.get(
            f"/api/applications/{self.application1.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["id"],
            self.application1.id
        )

        self.assertEqual(
            response.data["status"],
            "applied"
        )

    def test_candidate_cannot_view_another_candidate_application_detail(self):
        self.client.force_authenticate(
            user=self.candidate1
        )

        response = self.client.get(
            f"/api/applications/{self.application2.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    # =========================================================
    # DAY 19 - ATS WORKFLOW TESTS
    # =========================================================

    def test_employer_can_shortlist_candidate(self):
        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/",
            {
                "status": "shortlisted"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.application1.refresh_from_db()

        self.assertEqual(
            self.application1.status,
            "shortlisted"
        )

    def test_employer_can_schedule_interview(self):
        self.application1.status = "shortlisted"
        self.application1.save(
            update_fields=["status"]
        )

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/",
            {
                "status": "interview_scheduled"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.application1.refresh_from_db()

        self.assertEqual(
            self.application1.status,
            "interview_scheduled"
        )

    def test_employer_can_select_candidate(self):
        self.application1.status = "interview_scheduled"
        self.application1.save(
            update_fields=["status"]
        )

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/",
            {
                "status": "selected"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.application1.refresh_from_db()

        self.assertEqual(
            self.application1.status,
            "selected"
        )

    def test_employer_can_reject_candidate(self):
        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/",
            {
                "status": "rejected"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.application1.refresh_from_db()

        self.assertEqual(
            self.application1.status,
            "rejected"
        )

    def test_invalid_status_transition_is_rejected(self):
        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/",
            {
                "status": "selected"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.application1.refresh_from_db()

        self.assertEqual(
            self.application1.status,
            "applied"
        )

    def test_selected_application_is_locked(self):
        self.application1.status = "selected"
        self.application1.save(
            update_fields=["status"]
        )

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/",
            {
                "status": "rejected"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.application1.refresh_from_db()

        self.assertEqual(
            self.application1.status,
            "selected"
        )

    def test_rejected_application_is_locked(self):
        self.application1.status = "rejected"
        self.application1.save(
            update_fields=["status"]
        )

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/",
            {
                "status": "shortlisted"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.application1.refresh_from_db()

        self.assertEqual(
            self.application1.status,
            "rejected"
        )

    def test_employer_cannot_modify_another_employers_application(self):
        self.client.force_authenticate(
            user=self.employer2
        )

        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/",
            {
                "status": "shortlisted"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        self.application1.refresh_from_db()

        self.assertEqual(
            self.application1.status,
            "applied"
        )

    def test_candidate_cannot_update_application_status(self):
        self.client.force_authenticate(
            user=self.candidate1
        )

        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/",
            {
                "status": "shortlisted"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_status_change_creates_audit_record(self):
        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/applications/{self.application1.id}/status/",
            {
                "status": "shortlisted"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        history = ApplicationStatusHistory.objects.get(
            application=self.application1
        )

        self.assertEqual(
            history.old_status,
            "applied"
        )

        self.assertEqual(
            history.new_status,
            "shortlisted"
        )

        self.assertEqual(
            history.changed_by,
            self.employer1
        )

    def test_status_history_endpoint(self):
        self.client.force_authenticate(
            user=self.employer1
        )

        self.client.patch(
            f"/api/applications/{self.application1.id}/status/",
            {
                "status": "shortlisted"
            },
            format="json",
        )

        response = self.client.get(
            f"/api/applications/{self.application1.id}/history/"
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
            response.data["results"][0]["new_status"],
            "shortlisted"
        )

class JobManagementTests(APITestCase):

    def setUp(self):

        self.employer1 = User.objects.create_user(
            username="jobemployer1",
            email="jobemployer1@example.com",
            password="Employer@12345",
            role="employer",
        )

        self.employer2 = User.objects.create_user(
            username="jobemployer2",
            email="jobemployer2@example.com",
            password="Employer@12345",
            role="employer",
        )

        self.candidate = User.objects.create_user(
            username="jobcandidate",
            email="jobcandidate@example.com",
            password="Candidate@12345",
            role="candidate",
        )

        self.job = Job.objects.create(
            employer=self.employer1.employer,
            title="Python Developer",
            description="Backend development",
            required_skills="Python, Django",
            experience="1-2 years",
            salary_min=30000,
            salary_max=50000,
            location="Kochi",
            job_type="full_time",
            status="active",
        )

    def test_employer_can_create_job(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.post(
            "/api/jobs/create/",
            {
                "title": "Django Developer",
                "description": "Django backend development",
                "required_skills": "Python, Django, REST API",
                "experience": "1-3 years",
                "salary_min": 35000,
                "salary_max": 60000,
                "location": "Kochi",
                "job_type": "full_time",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.data["employer"],
            self.employer1.employer.id
        )

    def test_candidate_cannot_create_job(self):

        self.client.force_authenticate(
            user=self.candidate
        )

        response = self.client.post(
            "/api/jobs/create/",
            {
                "title": "Unauthorized Job",
                "description": "Should not be created",
                "required_skills": "Python",
                "experience": "1 year",
                "salary_min": 20000,
                "salary_max": 30000,
                "location": "Kochi",
                "job_type": "full_time",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_employer_can_update_own_job(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/jobs/{self.job.id}/",
            {
                "title": "Senior Python Developer"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.job.refresh_from_db()

        self.assertEqual(
            self.job.title,
            "Senior Python Developer"
        )

    def test_employer_cannot_update_other_employer_job(self):

        self.client.force_authenticate(
            user=self.employer2
        )

        response = self.client.patch(
            f"/api/jobs/{self.job.id}/",
            {
                "title": "Unauthorized Update"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_employer_can_deactivate_own_job(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/jobs/{self.job.id}/status/",
            {
                "status": "inactive"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.job.refresh_from_db()

        self.assertEqual(
            self.job.status,
            "inactive"
        )

    def test_employer_can_activate_own_job(self):

        self.job.status = "inactive"
        self.job.save()

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/jobs/{self.job.id}/status/",
            {
                "status": "active"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.job.refresh_from_db()

        self.assertEqual(
            self.job.status,
            "active"
        )

    def test_invalid_salary_range_is_rejected(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.post(
            "/api/jobs/create/",
            {
                "title": "Invalid Salary Job",
                "description": "Invalid salary test",
                "required_skills": "Python",
                "experience": "1 year",
                "salary_min": 60000,
                "salary_max": 30000,
                "location": "Kochi",
                "job_type": "full_time",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )