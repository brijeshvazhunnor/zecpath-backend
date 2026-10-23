# Day 32 — Background Jobs and Async Processing

## Objective

Integrate Celery and Redis with Django to support background task execution,
including notification delivery, resume parsing, AI interview-question
generation, and periodic jobs.

## Implementation

- Configured Celery in the Django project.
- Configured Redis as the message broker and result backend.
- Registered the existing application-notification task.
- Added `parse_resume_async` for background resume parsing and skill extraction.
- Added `generate_interview_questions_async` to call the existing interview
  question generation service from a worker.
- Added `periodic_queue_health_check` for aggregate system counts.
- Integrated `django-celery-beat` and its database-backed scheduler.
- Configured the health-check task to run every 15 minutes.
- Updated Python dependencies in `requirements.txt`.

## Verification Evidence

Previously observed during Day 32 development:

- Django system check completed without issues.
- Redis returned `PONG`.
- Celery worker registered all four tasks.
- The health-check task completed successfully through the worker.
- The result backend returned the task result from Redis.
- Celery Beat started using `DatabaseScheduler`.
- `pip check` reported no broken requirements.
- The existing core test suite passed: 102 tests.

Additional automated task tests are provided in
`apps/core/tests_background_tasks.py`. Their results must be recorded after
running the tests in the current environment.

## Task Results and Data Handling

The resume task returns summary metadata and detected skills rather than
returning the complete extracted resume text in the Celery result.

The AI task calls the existing interview-question generation service. Its
automated test mocks that service; this verifies task integration but does
not establish that a live AI provider request succeeds.

The health-check task returns aggregate counts only.

## Current Limitations

- Parsed resume text and generated questions are not persisted by these tasks.
- Live AI-provider execution must be tested separately with valid environment
  configuration.
- Periodic scheduler startup was observed; an actual Beat-triggered execution
  should be confirmed separately.
- Production email delivery is not established by the local console email
  backend.
- Redis and Celery worker availability are required for queued tasks to run.

## Git Deliverables

- Branch: `day32-background-jobs-async`
- Initial implementation commit: `e4396b2`
- New verification test file: `apps/core/tests_background_tasks.py`
- Completion report: `docs/day32-background-jobs-report.md`

## Completion Criteria

Day 32 can be considered verified when the task tests pass, the worker
executes queued tasks, Beat successfully schedules a periodic execution,
and the changes are committed and pushed.
