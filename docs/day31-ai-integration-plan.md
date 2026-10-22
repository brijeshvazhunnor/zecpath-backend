# Day 31: AI Integration Plan

## 1. Purpose

Define a staged integration plan for adding AI-assisted voice interviews to the existing Zecpath recruitment backend.

This is an architecture and integration plan. The LLM, STT, TTS, voice-call provider, and interview orchestration described here are proposed components unless separately implemented and tested.

## 2. End-to-End Workflow

1. An employer creates and activates a job.
2. A candidate applies and the backend records the application.
3. Existing ATS logic calculates a suitability score and ranking.
4. Existing eligibility and shortlisting rules determine whether the application is shortlisted.
5. The backend verifies that the application is eligible for an interview and has no conflicting active interview.
6. The backend creates an interview record and enqueues an asynchronous task.
7. A Celery worker obtains the required job, application, and candidate data.
8. The LLM generates job-relevant questions and an evaluation rubric.
9. The system schedules the interview or requests an outbound call from the selected voice provider.
10. The voice service delivers prompts using TTS and captures candidate responses.
11. STT converts responses into text, which is associated with the relevant question.
12. An evaluation service scores answers against the configured rubric and stores supporting evidence.
13. The backend saves the interview outcome and emits a result notification.
14. Authorized users review the result and proceed according to the configured recruitment workflow.

## 3. Proposed Integration Boundaries

### Django REST API

Responsibilities:
- Authenticate and authorize the requesting user.
- Validate the application and interview request.
- Create an interview record with a stable identifier.
- Return an accepted response for asynchronous work.
- Expose authorized interview status and result endpoints.
- Receive verified provider webhooks.

The API should not wait for a complete external voice interview to finish.

### Celery workers

Responsibilities:
- Generate interview questions.
- Request or schedule a call.
- Process provider callbacks and transcripts.
- Request answer evaluation.
- Save results and trigger notifications.
- Retry eligible transient failures and record terminal failures.

The existing project already has Celery notification-task infrastructure. Dedicated interview tasks, queue configuration, and lifecycle handling would need to be added.

### AI services

LLM:
- Generate questions from job requirements and a predefined interview plan.
- Return structured output validated by the backend.
- Evaluate answers against a consistent rubric.
- Avoid using protected or irrelevant personal attributes in scoring.

STT:
- Convert recorded or streamed speech into text.
- Return transcription status and provider references.
- Handle low-confidence or unavailable transcriptions explicitly.

TTS:
- Render the question prompts as speech.
- Handle generation errors without corrupting interview state.

Voice provider:
- Schedule or initiate calls.
- Deliver call status webhooks.
- Associate each callback with the correct interview and call ID.
- Handle busy, unanswered, failed, and completed calls.

## 4. Synchronous vs. Asynchronous Processing

| Operation | Recommended mode | Reason |
|---|---|---|
| Authentication and request validation | Synchronous | Immediate response needed |
| Eligibility check and interview creation | Synchronous | Validate and persist before accepting work |
| Enqueue interview task | Synchronous request, asynchronous execution | Return promptly without waiting for providers |
| Question generation | Asynchronous | External LLM latency and transient failures |
| Call scheduling or initiation | Asynchronous | External provider interaction |
| Speech transcription | Asynchronous or provider callback-driven | Duration and external processing variability |
| Answer evaluation | Asynchronous | LLM latency and potential retries |
| Status and result retrieval | Synchronous API | Read persisted state |
| Result notification | Asynchronous | Notifications should not block interview processing |

## 5. Interview Lifecycle

Suggested states:

- `pending`: interview request created.
- `generating_questions`: questions are being prepared.
- `scheduled`: interview time is confirmed.
- `initiating_call`: the call request is being processed.
- `in_progress`: the interview has started.
- `processing_transcript`: speech is being transcribed.
- `evaluating`: answers are being evaluated.
- `completed`: result is saved successfully.
- `failed`: processing stopped after a terminal failure.
- `cancelled`: interview was cancelled.
- `reschedule_required`: the candidate or provider needs another attempt.

These are proposed interview-specific states. They are not a claim that the existing `Application` model already supports all of them. Keep interview lifecycle status separate from the application status and its status history.

## 6. Failure Handling and Retries

| Failure | Recommended handling |
|---|---|
| LLM rate limit or temporary service error | Retry with exponential backoff and jitter; respect provider retry instructions |
| Invalid LLM output | Validate schema; retry a limited number of times, then mark failed |
| Voice provider timeout | Check provider status using the stored request ID before creating another call |
| Busy or unanswered call | Apply configurable retry/rescheduling policy and attempt limit |
| STT failure | Retry if transient; preserve call state and provide a manual review path |
| Evaluation failure | Retry evaluation independently without placing another call |
| Notification failure | Retry notification separately from the interview workflow |
| Invalid or duplicate webhook | Verify signature and deduplicate; reject invalid signatures |
| Database failure | Roll back incomplete changes and retry only where safe |
| Exhausted retries | Record terminal failure, alert/log it, and expose a recoverable state |

The existing notification task uses Celery's retry capability with `max_retries=3`. This is useful precedent, but interview tasks need their own retry policies, time limits, and idempotency controls. A retry count alone does not guarantee safe processing.

## 7. Timeout Strategy

Define explicit, configurable timeouts for:
- LLM question generation.
- Voice-provider API requests.
- STT processing.
- LLM answer evaluation.
- Webhook acknowledgement.
- Overall interview processing.

Choose timeout values from the selected provider's documented limits and measured latency. Do not keep HTTP requests open while waiting for an entire call or interview to complete.

## 8. Idempotency and Duplicate Prevention

- Generate a unique interview ID before starting external work.
- Use an idempotency key for interview creation and call initiation where the provider supports it.
- Persist the external provider's call/request ID.
- Deduplicate webhooks using the provider event ID.
- Make each processing task safe to retry.
- Prevent duplicate calls when a worker retries after a timeout.
- Use database transactions for related state updates.
- Consider a transactional outbox if reliable event publication is required across database and broker boundaries.

## 9. Data Model Proposal

Potential future models:

### Interview
- Application foreign key.
- Interview status.
- Scheduled time and timezone.
- Provider and external call ID.
- Idempotency key.
- Started/completed timestamps.
- Failure code and safe diagnostic message.

### InterviewQuestion
- Interview foreign key.
- Question text.
- Related skill or competency.
- Evaluation rubric.
- Question sequence.

### InterviewResponse
- Question foreign key.
- Transcript text or protected storage reference.
- Transcription status.
- Optional confidence metadata.
- Created timestamp.

### InterviewEvaluation
- Interview or response foreign key.
- Rubric-based score.
- Explanation and evidence.
- Model/provider identifier.
- Evaluation version and timestamp.
- Review status.

These are proposed schema elements; inspect current models before implementation to avoid duplication.

## 10. Security, Privacy and Fairness

- Obtain appropriate consent before recording or processing candidate speech.
- Define retention and deletion rules for recordings and transcripts.
- Minimize data sent to external AI providers.
- Keep API keys in environment variables or a secrets manager.
- Authenticate and authorize interview endpoints.
- Verify webhook signatures and enforce replay protection.
- Restrict access to resumes, transcripts, and interview results.
- Log identifiers and status changes without exposing unnecessary personal data.
- Use consistent job-related rubrics and keep an auditable explanation of scores.
- Provide human review and a way to challenge or correct inaccurate transcripts.
- Assess applicable privacy, employment, and AI requirements before production deployment.

## 11. Suggested Implementation Phases

1. Confirm requirements, provider capabilities, cost, consent, and retention.
2. Design and migrate interview-related models.
3. Add authenticated interview creation, status, and result endpoints.
4. Implement a Celery task for question generation using a mock provider first.
5. Add provider adapters and request timeouts.
6. Add a voice-provider sandbox integration and verified webhook handling.
7. Add STT, transcript persistence, and question-to-answer mapping.
8. Add rubric-based evaluation and result storage.
9. Add retries, idempotency, monitoring, and failure recovery.
10. Test duplicate events, provider outages, unauthorized access, and complete workflows.
11. Run a controlled pilot with human review before considering production use.

## 12. Acceptance Criteria

- Only eligible, authorized applications can request interviews.
- An interview request persists before background execution starts.
- The API returns promptly without waiting for an interview to finish.
- Each interview and external call can be traced using stable identifiers.
- Duplicate requests and webhooks do not create duplicate interviews or calls.
- Transcription and evaluation failures can be retried independently.
- Terminal failures are recorded and visible to authorized operators.
- Scores have a rubric and supporting evidence.
- Sensitive interview data has defined access and retention controls.
- Automated tests cover success, timeout, retry, duplicate-event, and authorization paths.
