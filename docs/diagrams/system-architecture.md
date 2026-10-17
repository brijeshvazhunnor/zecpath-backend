# System Architecture

This diagram illustrates the main components of the Zecpath recruitment backend and their interactions.

```mermaid
flowchart TD
    C[Candidate] --> API[Django REST API]
    E[Employer / Recruiter] --> API
    A[Administrator] --> API

    API --> AUTH[JWT Authentication and Permissions]
    AUTH --> JOBS[Job Management]
    AUTH --> APP[Application Management]
    AUTH --> PROFILE[Candidate Profiles and Resume Upload]

    APP --> ATS[Resume Parsing and ATS Scoring]
    ATS --> RANK[Candidate Ranking]
    RANK --> SHORT[Automated Shortlisting]
    SHORT --> STATUS[Application Status and History]

    JOBS --> DB[(SQLite Database)]
    APP --> DB
    PROFILE --> DB
    ATS --> DB
    SHORT --> DB
    STATUS --> DB

    PROFILE --> MEDIA[Resume Media Storage]
    SHORT --> NOTIFY[Notification Tasks]
    NOTIFY --> CELERY[Celery Worker]
    CELERY --> REDIS[Redis Broker]
    CELERY --> LOG[Notification Logs]
    LOG --> DB

    API --> ANALYTICS[Employer Analytics]
    ANALYTICS --> DB
```
## Component responsibilities

- **Django REST API:** Exposes recruitment endpoints.
- **JWT authentication and permissions:** Protects endpoints according to user roles.
- **Job management:** Supports employer job creation and management.
- **Application management:** Handles candidate applications and status history.
- **Resume processing and ATS:** Parses resumes, compares skills, and calculates application scores.
- **Automated shortlisting:** Applies configured rules to application scores.
- **Celery and Redis:** Support asynchronous notification processing when configured and running.
- **Database and media storage:** Store application records and uploaded resumes.

This is a logical architecture diagram, not a deployment diagram. Actual production infrastructure may differ.
