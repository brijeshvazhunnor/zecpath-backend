# Day 29 — Testing, Security Audit & Bug Fixing

## Objective
Improve backend reliability by testing resume-upload security, validating uploaded document contents, and running regression checks.

## Security improvements
- Enforced the 5 MB maximum resume upload size.
- Restricted resume uploads to PDF and DOCX extensions.
- Added PDF parsing validation to reject malformed PDFs and documents with no pages.
- Added DOCX archive and document parsing validation.
- Reset the uploaded file pointer after validation so downstream processing can read the file.
- Kept resume-upload access restricted by authentication, candidate role, and profile ownership.

## Automated tests
Added `ResumeUploadSecurityTests` covering:
1. Unauthenticated upload rejection.
2. Employer upload rejection.
3. Unsupported extension rejection.
4. Oversized file rejection.
5. Malformed PDF rejection.
6. Malformed DOCX rejection.
7. Successful valid PDF upload by a candidate.
8. Employer access to a candidate's resume rejection.

## Verification results
- `python manage.py test apps.core -v 1`: 83 tests passed.
- `python manage.py check`: passed.
- `python manage.py makemigrations --check`: no changes detected.
- `git diff --check`: passed.

## Scope and limitations
These checks cover the tested Django API paths and resume-upload validation. They do not constitute a complete penetration test or production security certification. Further review should include deployment configuration, media-file access controls, secrets management, dependency vulnerabilities, and authorization tests across all API endpoints.

## Outcome
Resume-upload validation has been strengthened, and the existing `apps.core` test suite passes. The changes require final code review and commit.
