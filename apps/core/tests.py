from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from apps.core.models import (
    Job,
    Application,
    Resume,
    ApplicationStatusHistory,
    Candidate,
    Employer,
)
User = get_user_model()
from django.test import TestCase

from apps.core.services.resume_nlp import (
    tokenize_text,
    extract_skills,
    extract_experience_years,
    extract_roles,
    extract_education,
    analyze_resume_text,
)


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


class EmployerDashboardTests(APITestCase):

    def setUp(self):

        self.employer1 = User.objects.create_user(
            username="dashboard_employer1",
            email="dashboard_employer1@example.com",
            password="Employer@12345",
            role="employer",
        )

        self.employer2 = User.objects.create_user(
            username="dashboard_employer2",
            email="dashboard_employer2@example.com",
            password="Employer@12345",
            role="employer",
        )

        self.candidate1 = User.objects.create_user(
            username="dashboard_candidate1",
            email="dashboard_candidate1@example.com",
            password="Candidate@12345",
            role="candidate",
        )

        self.candidate2 = User.objects.create_user(
            username="dashboard_candidate2",
            email="dashboard_candidate2@example.com",
            password="Candidate@12345",
            role="candidate",
        )

        self.candidate3 = User.objects.create_user(
            username="dashboard_candidate3",
            email="dashboard_candidate3@example.com",
            password="Candidate@12345",
            role="candidate",
        )

        self.job1 = Job.objects.create(
            employer=self.employer1.employer,
            title="Python Backend Developer",
            description="Python Django backend development",
            location="Kochi",
            required_skills="Python, Django, REST API",
            experience="0-2 years",
            status=Job.Status.ACTIVE,
        )

        self.job2 = Job.objects.create(
            employer=self.employer1.employer,
            title="Machine Learning Engineer",
            description="Machine learning and AI development",
            location="Bangalore",
            required_skills="Python, Machine Learning, TensorFlow",
            experience="1-3 years",
            status=Job.Status.INACTIVE,
        )

        self.job3 = Job.objects.create(
            employer=self.employer2.employer,
            title="Java Developer",
            description="Java backend development",
            location="Chennai",
            required_skills="Java, Spring",
            experience="2-4 years",
            status=Job.Status.ACTIVE,
        )

        # Candidate 1 profile
        self.candidate1.candidate.full_name = "Python Candidate"
        self.candidate1.candidate.skills = "Python, Django, REST API"
        self.candidate1.candidate.save()

        # Candidate 2 profile
        self.candidate2.candidate.full_name = "ML Candidate"
        self.candidate2.candidate.skills = (
            "Python, Machine Learning, TensorFlow"
        )
        self.candidate2.candidate.save()

        # Candidate 3 profile
        self.candidate3.candidate.full_name = "Backend Candidate"
        self.candidate3.candidate.skills = "Python, Django, REST API"
        self.candidate3.candidate.save()

        # Application 1
        self.application1 = Application.objects.create(
            job=self.job1,
            candidate=self.candidate1.candidate,
            status="applied",
        )

        # Application 2
        self.application2 = Application.objects.create(
            job=self.job1,
            candidate=self.candidate2.candidate,
            status="shortlisted",
        )

        # Application 3
        # Candidate 3 is used because candidate 1 already
        # applied to job 1 above.
        self.application3 = Application.objects.create(
            job=self.job1,
            candidate=self.candidate3.candidate,
            status="interview_scheduled",
        )

        # Application 4
        # Different job belonging to the same employer.
        self.application4 = Application.objects.create(
            job=self.job2,
            candidate=self.candidate2.candidate,
            status="selected",
        )

        # Application belonging to another employer.
        self.application_other_employer = Application.objects.create(
            job=self.job3,
            candidate=self.candidate1.candidate,
            status="rejected",
        )

    def test_employer_can_view_own_jobs(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.get(
            "/api/employer/jobs/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        job_ids = [
            job["id"]
            for job in response.data["results"]
        ]

        self.assertIn(
            self.job1.id,
            job_ids
        )

        self.assertIn(
            self.job2.id,
            job_ids
        )

        self.assertNotIn(
            self.job3.id,
            job_ids
        )

    def test_employer_cannot_edit_another_employers_job(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/employer/jobs/{self.job3.id}/",
            {
                "title": "Unauthorized Update"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        self.job3.refresh_from_db()

        self.assertEqual(
            self.job3.title,
            "Java Developer"
        )

    def test_employer_can_edit_own_job(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/employer/jobs/{self.job1.id}/",
            {
                "title": "Senior Python Backend Developer"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.job1.refresh_from_db()

        self.assertEqual(
            self.job1.title,
            "Senior Python Backend Developer"
        )

    def test_employer_can_close_own_job(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/employer/jobs/{self.job1.id}/close/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.job1.refresh_from_db()

        self.assertEqual(
            self.job1.status,
            Job.Status.INACTIVE
        )

    def test_employer_cannot_close_another_employers_job(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.patch(
            f"/api/employer/jobs/{self.job3.id}/close/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        self.job3.refresh_from_db()

        self.assertEqual(
            self.job3.status,
            Job.Status.ACTIVE
        )

    def test_employer_can_view_own_applicants_only(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.get(
            "/api/employer/applicants/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        application_ids = [
            application["id"]
            for application in response.data["results"]
        ]

        self.assertIn(
            self.application1.id,
            application_ids
        )

        self.assertIn(
            self.application2.id,
            application_ids
        )

        self.assertIn(
            self.application3.id,
            application_ids
        )

        self.assertIn(
            self.application4.id,
            application_ids
        )

        self.assertNotIn(
            self.application_other_employer.id,
            application_ids
        )

    def test_employer_can_filter_applicants_by_status(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.get(
            "/api/employer/applicants/?status=shortlisted"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            len(response.data["results"]),
            1
        )

        self.assertEqual(
            response.data["results"][0]["status"],
            "shortlisted"
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            self.application2.id
        )

    def test_employer_can_search_applicants(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.get(
            "/api/employer/applicants/?search=Machine"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        application_ids = [
            application["id"]
            for application in response.data["results"]
        ]

        self.assertIn(
            self.application2.id,
            application_ids
        )

        self.assertIn(
            self.application4.id,
            application_ids
        )

    def test_employer_analytics_contains_correct_counts(self):

        self.client.force_authenticate(
            user=self.employer1
        )

        response = self.client.get(
            "/api/employer/analytics/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["total_jobs"],
            2
        )

        self.assertEqual(
            response.data["active_jobs"],
            1
        )

        self.assertEqual(
            response.data["closed_jobs"],
            1
        )

        self.assertEqual(
            response.data["total_applications"],
            4
        )

        self.assertEqual(
            response.data["shortlisted_applications"],
            1
        )

        self.assertEqual(
            response.data["interview_scheduled"],
            1
        )

        self.assertEqual(
            response.data["selected_applications"],
            1
        )

        self.assertEqual(
            response.data["rejected_applications"],
            0
        )

        self.assertEqual(
            response.data["shortlist_ratio"],
            25.0
        )

    def test_employer_analytics_excludes_other_employers(self):

        self.client.force_authenticate(
            user=self.employer2
        )

        response = self.client.get(
            "/api/employer/analytics/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["total_jobs"],
            1
        )

        self.assertEqual(
            response.data["total_applications"],
            1
        )

        self.assertEqual(
            response.data["rejected_applications"],
            1
        )

    def test_candidate_cannot_access_employer_analytics(self):

        self.client.force_authenticate(
            user=self.candidate1
        )

        response = self.client.get(
            "/api/employer/analytics/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

# =========================================================
# DAY 21 - CANDIDATE DASHBOARD TESTS
# =========================================================

class CandidateDashboardTests(APITestCase):

    def setUp(self):
        self.employer = User.objects.create_user(
            username="candidate_test_employer",
            email="candidate_test_employer@example.com",
            password="Employer@12345",
            role="employer",
        )

        self.candidate = User.objects.create_user(
            username="candidate_test_user",
            email="candidate_test_user@example.com",
            password="Candidate@12345",
            role="candidate",
        )

        self.other_candidate = User.objects.create_user(
            username="other_candidate",
            email="other_candidate@example.com",
            password="Candidate@12345",
            role="candidate",
        )

        self.employer_profile = self.employer.employer
        self.employer_profile.company_name = "Test Company"
        self.employer_profile.save()

        self.candidate_profile = self.candidate.candidate
        self.candidate_profile.full_name = "Test Candidate"
        self.candidate_profile.skills = "Python, Django, REST API, SQL"
        self.candidate_profile.experience = "1 year"
        self.candidate_profile.education = "MSc Computer Science"
        self.candidate_profile.save()

        self.other_candidate_profile = self.other_candidate.candidate
        self.other_candidate_profile.full_name = "Other Candidate"
        self.other_candidate_profile.skills = "Java, Spring"
        self.other_candidate_profile.save()

        self.job = Job.objects.create(
            employer=self.employer_profile,
            title="Python Django Developer",
            description="Backend development using Python and Django.",
            required_skills="Python, Django, REST API, PostgreSQL",
            experience="1-2 years",
            salary_min=25000,
            salary_max=40000,
            location="Kochi",
            job_type=Job.JobType.FULL_TIME,
            status=Job.Status.ACTIVE,
        )

        self.second_job = Job.objects.create(
            employer=self.employer_profile,
            title="Python Backend Developer",
            description="Python backend development.",
            required_skills="Python, Django",
            experience="0-1 years",
            salary_min=20000,
            salary_max=35000,
            location="Kochi",
            job_type=Job.JobType.FULL_TIME,
            status=Job.Status.ACTIVE,
        )

        self.unmatched_job = Job.objects.create(
            employer=self.employer_profile,
            title="Java Developer",
            description="Java backend development.",
            required_skills="Java, Spring, Hibernate",
            experience="2-3 years",
            salary_min=30000,
            salary_max=50000,
            location="Bangalore",
            job_type=Job.JobType.FULL_TIME,
            status=Job.Status.ACTIVE,
        )

        self.closed_job = Job.objects.create(
            employer=self.employer_profile,
            title="Closed Python Job",
            description="This job is no longer active.",
            required_skills="Python, Django",
            experience="1 year",
            location="Kochi",
            job_type=Job.JobType.FULL_TIME,
            status=Job.Status.INACTIVE,
        )

    # ---------------------------------------------------------
    # CANDIDATE APPLICATIONS
    # ---------------------------------------------------------

    def test_candidate_can_view_own_applications(self):
        application = Application.objects.create(
            job=self.job,
            candidate=self.candidate_profile,
        )

        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(
            "/api/candidate/applications/"
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
            application.id
        )

    def test_candidate_cannot_view_another_candidate_application(self):
        Application.objects.create(
            job=self.job,
            candidate=self.other_candidate_profile,
        )

        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(
            "/api/candidate/applications/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["count"],
            0
        )

    # ---------------------------------------------------------
    # INTERVIEW STATUS
    # ---------------------------------------------------------

    def test_candidate_can_view_interview_applications(self):
        Application.objects.create(
            job=self.job,
            candidate=self.candidate_profile,
            status="interview_scheduled",
        )

        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(
            "/api/candidate/interviews/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["count"],
            1
        )

    # ---------------------------------------------------------
    # SAVED JOBS
    # ---------------------------------------------------------

    def test_candidate_can_save_job(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.post(
            "/api/candidate/saved-jobs/",
            {"job": self.job.id},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.data["job"],
            self.job.id
        )

    def test_candidate_cannot_save_same_job_twice(self):
        self.client.force_authenticate(user=self.candidate)

        self.client.post(
            "/api/candidate/saved-jobs/",
            {"job": self.job.id},
            format="json",
        )

        response = self.client.post(
            "/api/candidate/saved-jobs/",
            {"job": self.job.id},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_candidate_can_remove_saved_job(self):
        self.client.force_authenticate(user=self.candidate)

        save_response = self.client.post(
            "/api/candidate/saved-jobs/",
            {"job": self.job.id},
            format="json",
        )

        self.assertEqual(
            save_response.status_code,
            status.HTTP_201_CREATED
        )

        response = self.client.delete(
            f"/api/candidate/saved-jobs/{self.job.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

    # ---------------------------------------------------------
    # SECURITY
    # ---------------------------------------------------------

    def test_employer_cannot_access_candidate_applications(self):
        self.client.force_authenticate(user=self.employer)

        response = self.client.get(
            "/api/candidate/applications/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_employer_cannot_access_candidate_recommendations(self):
        self.client.force_authenticate(user=self.employer)

        response = self.client.get(
            "/api/candidate/recommendations/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    # ---------------------------------------------------------
    # RECOMMENDATIONS
    # ---------------------------------------------------------

    def test_candidate_recommendations_return_matching_jobs(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(
            "/api/candidate/recommendations/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        job_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            self.job.id,
            job_ids
        )

        self.assertIn(
            self.second_job.id,
            job_ids
        )

        self.assertNotIn(
            self.closed_job.id,
            job_ids
        )

    def test_applied_job_is_excluded_from_recommendations(self):
        Application.objects.create(
            job=self.job,
            candidate=self.candidate_profile,
        )

        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(
            "/api/candidate/recommendations/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        job_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertNotIn(
            self.job.id,
            job_ids
        )

    def test_recommendation_contains_skill_match_score(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(
            "/api/candidate/recommendations/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        recommendation = next(
            item
            for item in response.data["results"]
            if item["id"] == self.job.id
        )

        self.assertEqual(
            recommendation["match_score"],
            75.0
        )

        self.assertEqual(
            sorted(recommendation["matched_skills"]),
            ["django", "python", "rest api"]
        )

    # ---------------------------------------------------------
    # APPLICATION TIMELINE
    # ---------------------------------------------------------

    def test_candidate_can_view_application_timeline(self):
        application = Application.objects.create(
            job=self.job,
            candidate=self.candidate_profile,
        )

        ApplicationStatusHistory.objects.create(
            application=application,
            old_status="",
            new_status="applied",
            changed_by=self.candidate,
            action="Application submitted",
        )

        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(
            f"/api/candidate/applications/{application.id}/timeline/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["count"],
            1
        )

    def test_candidate_cannot_view_another_candidate_timeline(self):
        application = Application.objects.create(
            job=self.job,
            candidate=self.other_candidate_profile,
        )

        ApplicationStatusHistory.objects.create(
            application=application,
            old_status="",
            new_status="applied",
            changed_by=self.other_candidate,
            action="Application submitted",
        )

        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(
            f"/api/candidate/applications/{application.id}/timeline/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["count"],
            0
        )

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.services.resume_cleaner import clean_resume_text
from apps.core.services.resume_parser import get_file_extension


class ResumeParserUtilityTests(APITestCase):

    def test_get_pdf_extension(self):
        self.assertEqual(
            get_file_extension("resume.pdf"),
            ".pdf"
        )

    def test_get_docx_extension(self):
        self.assertEqual(
            get_file_extension("resume.docx"),
            ".docx"
        )

    def test_clean_resume_text(self):

        raw_text = """
        John Doe


        Python     Django


        PostgreSQL
        """

        cleaned = clean_resume_text(raw_text)

        self.assertEqual(
            cleaned,
            "John Doe\nPython Django\nPostgreSQL"
        )

class ResumeNLPTests(TestCase):

    def test_tokenization(self):

        text = "Python Django Developer"

        tokens = tokenize_text(text)

        self.assertIn(
            "Python",
            tokens
        )

        self.assertIn(
            "Django",
            tokens
        )

        self.assertIn(
            "Developer",
            tokens
        )


    def test_skill_extraction(self):

        text = """
        Python Django PostgreSQL TensorFlow Docker
        """

        skills = extract_skills(text)

        self.assertIn(
            "Python",
            skills
        )

        self.assertIn(
            "Django",
            skills
        )

        self.assertIn(
            "PostgreSQL",
            skills
        )

        self.assertIn(
            "TensorFlow",
            skills
        )


    def test_experience_extraction(self):

        text = "I have 3 years of experience in Python."

        years = extract_experience_years(text)

        self.assertEqual(
            years,
            3
        )


    def test_role_detection(self):

        text = "Python Developer and Machine Learning Engineer"

        roles = extract_roles(text)

        self.assertIn(
            "Python Developer",
            roles
        )

        self.assertIn(
            "Machine Learning Engineer",
            roles
        )


    def test_education_extraction(self):

        text = """
        MSc Computer Science
        BSc Computer Science
        """

        education = extract_education(text)

        self.assertTrue(
            len(education) >= 2
        )


    def test_complete_resume_analysis(self):

        text = """
        Python Backend Developer

        2 years of experience in Python development.

        Skills:
        Python, Django, PostgreSQL, Docker.

        Education:
        MSc Computer Science
        """

        result = analyze_resume_text(text)

        self.assertIn(
            "skills",
            result
        )

        self.assertIn(
            "experience",
            result
        )

        self.assertIn(
            "education",
            result

        )

        self.assertIn(
            "Python",
            result["skills"]
        )

        self.assertEqual(
            result["experience"]["years"],
            2
        )