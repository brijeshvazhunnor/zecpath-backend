# Day 28 — Performance Optimization and Scaling

## 1. Objective

Improve backend database efficiency, verify that existing functionality
remains correct, and identify further performance and scalability work
for the Zecpath hiring platform.

## 2. Development Environment

- Framework: Django REST Framework
- Database: SQLite
- Database file size at inspection: 424 KB
- Jobs at inspection: 3
- Applications at inspection: 3
- ATS scores at inspection: 3
- Notification logs at inspection: 1
- Load-testing tools: Locust and Django Debug Toolbar were not installed

The dataset is small and represents development data, not production load.

## 3. Optimization Implemented

### Employer Analytics API

Endpoint: `/api/employer/analytics/`

The original implementation performed eight separate COUNT queries:
- Total jobs
- Active jobs
- Closed jobs
- Total applications
- Shortlisted applications
- Scheduled interviews
- Selected applications
- Rejected applications

The implementation was changed to use conditional aggregation:
- One aggregate query calculates job counts.
- One aggregate query calculates application counts.

This reduces the analytics aggregation from eight separate count queries
to two aggregate queries, excluding other queries that may occur during
request authentication or processing.

The existing response fields and shortlist-ratio calculation were
preserved.

## 4. Regression Testing

Added a regression test to verify that the employer analytics endpoint
executes the expected two aggregate queries.

Validation results:
- `python manage.py check`: passed
- `python manage.py test apps.core.tests.EmployerDashboardTests`: 12 passed
- `python manage.py test apps.core`: 75 passed
- `python manage.py makemigrations --check`: no changes detected
- `git diff --check`: passed

## 5. Performance Measurements and Limitations

The verified result is a reduction in analytics aggregation query count.

A controlled before-and-after measurement of endpoint response time has
not yet been performed. The full test suite's runtime is not a reliable
measure of the analytics endpoint's individual latency.

The development database contains only a few records. It is insufficient
to establish production throughput, concurrency limits, or performance
under heavy traffic.

No load test has been completed yet.

## 6. Further Optimization Opportunities

1. Profile ATS ranking, which currently recalculates and saves scores
   for each eligible application during a ranking request.
2. Evaluate query plans and existing indexes against representative data.
3. Benchmark endpoint latency and query counts with a larger dataset.
4. Perform controlled concurrent-request load testing.
5. Evaluate caching only where invalidation and data freshness can be
   maintained safely.
6. Assess PostgreSQL and production deployment configuration separately
   from the current SQLite development setup.

## 7. Git Deliverable

Branch: `day28-performance-optimization`

Analytics optimization commit:
`8b6d58a perf: optimize employer analytics queries`

The performance report is a separate documentation deliverable.

## 6.1 Initial Employer Analytics Benchmark

Endpoint: `/api/employer/analytics/`

Method:
- One warm-up request, excluded from measurements.
- 30 measured requests.
- Django REST Framework APIClient with in-process forced
  authentication for an existing employer user.
- SQL queries captured with Django's CaptureQueriesContext.

Observed results:
- Successful requests: 30/30 (HTTP 200)
- Median response time: 2.86 ms
- P95 response time: 5.70 ms
- Minimum response time: 2.52 ms
- Maximum response time: 5.97 ms
- Median SQL queries per request: 2
- Aggregate queries per request: 2

Limitations:
- This is a local development measurement using SQLite and a small dataset.
- Forced authentication bypasses JWT token validation and login overhead.
- The measurements do not represent concurrent traffic or production latency.
- No equivalent measurement of the original implementation was taken,
  so these figures do not establish a before-and-after latency improvement.
