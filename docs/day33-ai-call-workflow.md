flowchart TD
    A[Candidate submits application] --> B[ATS scoring]
    B --> C{Automatic shortlisting}
    C -->|Not shortlisted| D[Remain under review or rejected]
    C -->|Shortlisted| E[Trigger AI call eligibility]

    E --> F{Job active?}
    F -->|No| X[Not eligible]
    F -->|Yes| G{Candidate active?}

    G -->|No| X
    G -->|Yes| H{Consent given?}

    H -->|No| X
    H -->|Yes| I{Available for AI call?}

    I -->|No| X
    I -->|Yes| J{ATS threshold met?}

    J -->|No| X
    J -->|Yes| K[Create AICall record]

    K --> L[Calculate next calling time]
    L --> M[Schedule Celery task]
    M --> N[Redis message broker]
    N --> O[Celery worker]
    O --> P{Task successful?}

    P -->|Yes| Q[Status: Queued]
    P -->|No| R[Retry with backoff]
    R --> S{Retries exhausted?}
    S -->|No| O
    S -->|Yes| T[Status: Failed]
