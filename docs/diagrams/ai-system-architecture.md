# Day 31: AI System Architecture and Workflow Design

## 1. Objective

Design how AI services, voice-call infrastructure, Django backend APIs, background workers, and persistent storage could work together in the Zecpath recruitment platform.

This document describes the existing backend and a proposed future AI interview integration. Proposed integrations are design recommendations, not claims that the integrations have already been implemented.

## 2. Current Capabilities and Proposed Components

### Existing backend capabilities

- Django REST Framework APIs.
- Candidate, employer, job, and application workflows.
- ATS scoring and candidate ranking.
- Eligibility checks and configurable shortlisting.
- Application status history.
- Notification logging and Celery notification tasks.
- Database-backed recruitment records.

### Proposed AI interview capabilities

- LLM-based interview question generation.
- Voice-call provider integration.
- Speech-to-text (STT).
- Text-to-speech (TTS).
- AI answer evaluation and interview scoring.
- Interview scheduling and result notifications.

These AI interview integrations require implementation and provider selection.

## 3. High-Level Architecture

```mermaid
flowchart TB
    subgraph Clients
        E[Employer Dashboard]
        C[Candidate Portal]
        A[Administrator]
    end

    subgraph Backend["Django Backend"]
        API[Django REST APIs]
        AUTH[Authentication and Permissions]
        ATS[ATS Scoring and Ranking]
        SHORT[Eligibility and Shortlisting]
        INTERVIEW[Proposed Interview Orchestrator]
    end

    subgraph Async["Asynchronous Processing"]
        BROKER[Message Broker]
        WORKER[Celery Workers]
        RETRY[Retry and Failure Handling]
    end

    subgraph AI["Proposed External AI Services"]
        LLM[LLM Question Generation and Evaluation]
        CALL[Voice Call Provider]
        STT[Speech-to-Text]
        TTS[Text-to-Speech]
    end

    subgraph Storage["Persistence"]
        DB[(Relational Database)]
        FILES[(Resume and Recording Storage)]
        LOGS[Task and Integration Logs]
    end

    E --> API
    C --> API
    A --> API
    API --> AUTH
    API --> ATS
    ATS --> SHORT
    SHORT --> DB
    API --> DB
    SHORT --> INTERVIEW
    INTERVIEW --> DB
    INTERVIEW --> BROKER
    BROKER --> WORKER
    WORKER --> LLM
    WORKER --> CALL
    WORKER --> STT
    WORKER --> TTS
    WORKER --> DB
    WORKER --> FILES
    WORKER --> RETRY
    RETRY --> BROKER
    WORKER --> LOGS
```

## 4. Proposed AI Call Sequence

```mermaid
sequenceDiagram
    actor Employer
    participant API as Django API
    participant DB as Database
    participant Queue as Celery Broker
    participant Worker as Celery Worker
    participant LLM as LLM Service
    participant Voice as Voice Provider
    participant STT as Speech-to-Text
    participant Eval as AI Evaluator

    Employer->>API: Request AI interview for shortlisted candidate
    API->>DB: Validate application and interview state
    DB-->>API: Application details
    API->>DB: Create interview record
    API->>Queue: Enqueue interview initiation
    API-->>Employer: Accepted for background processing

    Queue->>Worker: Execute interview task
    Worker->>LLM: Generate questions from job and skills
    LLM-->>Worker: Questions and evaluation criteria
    Worker->>DB: Save interview configuration
    Worker->>Voice: Initiate scheduled/outbound call
    Voice-->>Worker: Call reference or initiation failure

    Note over Voice,STT: Candidate answers during the call
    Voice->>STT: Audio or recording reference
    STT-->>Worker: Transcribed answers
    Worker->>DB: Store transcript and progress

    Worker->>Eval: Evaluate answers against criteria
    Eval-->>Worker: Scores, evidence and feedback
    Worker->>DB: Save result and interview status
    Worker->>Queue: Enqueue result notification
```

## 5. AI Scoring Data Flow

```mermaid
flowchart TD
    JOB[Job Description and Required Skills]
    RESUME[Candidate Resume and Profile]
    ATS[Existing ATS Scoring]
    SHORT[Existing Shortlisting Decision]
    CONFIG[Interview Configuration]
    QGEN[Proposed LLM Question Generation]
    CALL[Proposed Voice Interview]
    TRANSCRIPT[Proposed STT Transcript]
    EVAL[Proposed AI Answer Evaluation]
    REVIEW[Optional Human Review]
    RESULT[Interview Result]
    DB[(Database)]
    NOTIFY[Notification Service]

    JOB --> ATS
    RESUME --> ATS
    ATS --> SHORT
    SHORT --> CONFIG
    JOB --> CONFIG
    CONFIG --> QGEN
    QGEN --> CALL
    CALL --> TRANSCRIPT
    TRANSCRIPT --> EVAL
    JOB --> EVAL
    CONFIG --> EVAL
    EVAL --> REVIEW
    REVIEW --> RESULT
    RESULT --> DB
    RESULT --> NOTIFY
```

The proposed interview score is a separate result from the existing ATS score. Any combined score or hiring decision requires an explicitly defined, validated policy; an AI score should not automatically determine hiring outcomes without appropriate oversight.

## 6. Service Interaction and Responsibility

| Component | Responsibility | Status |
|---|---|---|
| Django REST API | Authenticate users and expose recruitment endpoints | Existing |
| ATS service | Match candidate profiles to job requirements | Existing |
| Shortlisting service | Apply configured eligibility and shortlisting rules | Existing |
| Relational database | Store jobs, applications, ATS scores and status history | Existing |
| Celery and broker | Run background work and coordinate tasks | Existing notification-task infrastructure; interview tasks proposed |
| LLM provider | Generate interview questions and evaluate answers | Proposed |
| Voice provider | Place calls and report call events | Proposed |
| STT provider | Convert candidate speech into text | Proposed |
| TTS provider | Convert prompts into speech | Proposed |
| Interview orchestration | Track interview lifecycle and coordinate services | Proposed |
| Recording/object storage | Store recordings if required and consented to | Proposed |

## 7. Design Principles

- Keep external AI and voice-provider calls outside ordinary API request processing.
- Persist interview state before enqueueing work.
- Use explicit timeouts, bounded retries, and idempotency keys.
- Verify incoming provider webhooks before processing them.
- Store provider request IDs and correlation IDs for tracing.
- Protect resumes, transcripts, recordings, and personal data.
- Record the evidence and rubric behind scores.
- Keep hiring decisions reviewable and configurable.
