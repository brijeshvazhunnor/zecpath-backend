# Zecpath Backend — API Reference

## Base URL

Local development:

`http://127.0.0.1:8000/api/`

All paths below are relative to this base URL.

## Authentication

The login endpoint accepts email and password and returns JWT `access` and `refresh` tokens.

For protected endpoints, use:

`Authorization: Bearer <access-token>`

Use the employer token for employer-owned job operations and the candidate token for candidate application operations. Exact permissions are enforced by each view.

## Authentication endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/signup/` | Register an account |
| POST | `/auth/login/` | Obtain JWT tokens using email and password |
| POST | `/auth/refresh/` | Refresh an access token |
| POST | `/auth/logout/` | Blacklist a refresh token |

## Job endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/jobs/create/` | Create a job as an employer |
| GET | `/jobs/` | List jobs |
| GET | `/jobs/featured/` | List featured jobs |
| GET | `/jobs/latest/` | List latest jobs |
| `/` | `/jobs/<id>/` | Job detail/update route; verify supported methods in the view |
| `/` | `/jobs/<id>/status/` | Job status route; verify supported methods in the view |
| GET | `/employer/jobs/` | Employer job list |
| `/` | `/employer/jobs/<id>/` | Employer job update route |
| `/` | `/employer/jobs/<id>/close/` | Close an employer job |

Job creation accepts fields including `title`, `description`, `required_skills`, `experience`, `salary_min`, `salary_max`, `location`, `job_type`, `status`, and `featured`.

Valid job types:

- `full_time`
- `part_time`
- `contract`
- `internship`
- `temporary`

Job status choices include `active` and `inactive`.

## Candidate and resume endpoints

| Method | Path | Purpose |
|---|---|---|
| `/` | `/profile/candidate/` | Retrieve or update candidate profile |
| `/` | `/profile/employer/` | Retrieve or update employer profile |
| POST | `/profile/resume/upload/` | Upload a resume |
| `/` | `/profile/resume/` | Resume endpoint; verify supported methods in the view |
| POST | `/jobs/<job_id>/apply/` | Apply for an active job |
| GET | `/candidate/applications/` | Candidate application list |
| GET | `/candidate/applications/<id>/` | Candidate application detail |
| GET | `/candidate/applications/<id>/timeline/` | Application timeline |
| GET | `/candidate/interviews/` | Candidate interview list |
| `/` | `/candidate/saved-jobs/` | List or create saved jobs |
| DELETE | `/candidate/saved-jobs/<job_id>/` | Remove a saved job |
| GET | `/candidate/recommendations/` | Candidate recommendations |

A candidate must have an active resume to apply. Duplicate applications are rejected, and the target job must be active.

## ATS and shortlisting endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/jobs/<job_id>/applications/<application_id>/ats-score/` | Calculate and save an application's ATS score |
| GET | `/jobs/<job_id>/ats-ranking/` | Retrieve ranked candidates |
| POST | `/jobs/<job_id>/auto-shortlist/` | Process eligible applications using shortlisting rules |
| POST | `/applications/<application_id>/automate/` | Run application automation |
| POST | `/applications/<application_id>/status/` | Manually update application status |
| `/` | `/jobs/<job_id>/shortlisting-rules/` | Shortlisting rules endpoint; verify supported methods in the view |
| `/` | `/applications/<id>/history/` | Application status history |

ATS scoring and shortlisting operations require authorization. The ATS score and ranking views check that the user can manage the requested job.

## Resume processing

| Method | Path | Purpose |
|---|---|---|
| `/` | `/resume/parse/` | Resume text extraction |
| `/` | `/resume/analyze/` | Resume analysis |

Check the relevant view classes for accepted HTTP methods, request fields, and permissions before integrating these endpoints.

## Employer analytics

| Method | Path | Purpose |
|---|---|---|
| GET | `/employer/applicants/` | Employer applicant list |
| GET | `/employer/analytics/` | Employer analytics |

The analytics implementation and performance measurements are documented in `day28-performance-report.md`.

## Admin endpoints

| Path | Purpose |
|---|---|
| `/admin/employers/<id>/approve/` | Employer approval |
| `/admin/users/<id>/block/` | Block a user |
| `/admin/users/<id>/unblock/` | Unblock a user |
| `/admin/users/<id>/flag/` | Flag an account |
| `/admin/jobs/<id>/manage/` | Manage a job |
| `/admin/jobs/<id>/remove-spam/` | Remove a spam job |
| `/admin/monitoring/stats/` | Platform statistics |
| `/admin/monitoring/user-growth/` | User growth metrics |
| `/admin/monitoring/job-activity/` | Job activity metrics |
| `/admin/audit-logs/` | Audit logs |

Verify each admin view's supported HTTP methods and permission classes before use.

## Verified demo requests

### 1. Create a job

`POST /jobs/create/`

Authorization: employer Bearer token.

### 2. Apply for a job

`POST /jobs/4/apply/`

Authorization: candidate Bearer token.

### 3. Calculate ATS score

`POST /jobs/4/applications/4/ats-score/`

Authorization: employer Bearer token.

### 4. Retrieve ATS ranking

`GET /jobs/4/ats-ranking/`

Authorization: employer Bearer token.

### 5. Run automatic shortlisting

`POST /jobs/4/auto-shortlist/`

Authorization: employer Bearer token.

The Day 30 demo returned ATS score `100.0`, rank `1`, and final application status `shortlisted`.

## Documentation notes

- A `/` method marker means the route's exact supported methods have not been verified in this reference.
- URL patterns should be checked alongside view permissions and serializers.
- The manual application status route appears twice in `apps/core/urls.py`; review and remove redundant declarations in a separate code-cleanup change after checking route names and reverse lookups.
