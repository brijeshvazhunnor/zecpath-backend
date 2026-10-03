import re


# ============================================================
# PREDEFINED SKILLS LIBRARY
# ============================================================

SKILLS_LIBRARY = [
    # Programming Languages
    "Python",
    "C",
    "C++",
    "Java",
    "JavaScript",
    "TypeScript",
    "Go",
    "Rust",
    "PHP",
    "Ruby",
    "Kotlin",
    "Swift",

    # Web / Backend
    "Django",
    "Django REST Framework",
    "Flask",
    "FastAPI",
    "Spring Boot",
    "Node.js",
    "Express.js",
    "REST API",
    "GraphQL",

    # Frontend
    "HTML",
    "CSS",
    "React",
    "Angular",
    "Vue.js",

    # Databases
    "SQL",
    "MySQL",
    "PostgreSQL",
    "SQLite",
    "MongoDB",
    "Redis",

    # AI / ML
    "Artificial Intelligence",
    "Machine Learning",
    "Deep Learning",
    "Natural Language Processing",
    "NLP",
    "Computer Vision",
    "Generative AI",
    "Generative Artificial Intelligence",
    "Large Language Models",
    "LLM",
    "TensorFlow",
    "PyTorch",
    "Scikit-learn",
    "Keras",
    "Pandas",
    "NumPy",

    # Cloud / DevOps
    "AWS",
    "Amazon Web Services",
    "Google Cloud",
    "GCP",
    "Microsoft Azure",
    "Azure",
    "Docker",
    "Kubernetes",
    "Git",
    "GitHub",
    "CI/CD",

    # Data
    "Data Science",
    "Data Analysis",
    "Data Engineering",
    "Big Data",
    "Apache Spark",
    "Apache Kafka",

    # Other
    "Linux",
    "Windows",
    "Agile",
    "Scrum",
    "Machine Learning",
]


# ============================================================
# ROLE LIBRARY
# ============================================================

ROLE_LIBRARY = [
    "Software Engineer",
    "Software Developer",
    "Python Developer",
    "Python Backend Developer",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Django Developer",
    "Machine Learning Engineer",
    "ML Engineer",
    "AI Engineer",
    "AI/ML Engineer",
    "Data Scientist",
    "Data Analyst",
    "Data Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Web Developer",
    "Software Trainee",
    "Software Intern",
    "Machine Learning Intern",
    "AI Intern",
    "Python Intern",
    "Backend Intern",
    "Developer Intern",
]


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize_text(text):
    """
    Convert resume text into a list of tokens.

    Example:
        "Python Developer with 2 years experience"

    Returns:
        ["Python", "Developer", "with", "2", "years", "experience"]
    """

    if not text:
        return []

    return re.findall(r"\b[\w+#.-]+\b", text)


# ============================================================
# KEYWORD EXTRACTION
# ============================================================

def extract_keywords(text, keywords=None):
    """
    Extract predefined keywords from resume text.

    Matching is case-insensitive.
    """

    if not text:
        return []

    if keywords is None:
        keywords = SKILLS_LIBRARY

    found_keywords = []
    lower_text = text.lower()

    for keyword in keywords:
        if keyword.lower() in lower_text:
            found_keywords.append(keyword)

    return found_keywords


# ============================================================
# SKILL EXTRACTION
# ============================================================

def _build_skill_pattern(skill):
    """
    Build a regex pattern for a skill.

    Word boundaries are used where possible to avoid
    accidental partial matches.
    """

    escaped_skill = re.escape(skill)

    return rf"(?<!\w){escaped_skill}(?!\w)"


def extract_skills(text):
    """
    Extract skills from resume text using regex matching.

    Returns a unique list of detected skills.
    """

    if not text:
        return []

    found_skills = []

    for skill in SKILLS_LIBRARY:

        pattern = _build_skill_pattern(skill)

        if re.search(pattern, text, re.IGNORECASE):
            found_skills.append(skill)

    return found_skills


# ============================================================
# EXPERIENCE PARSING
# ============================================================

def extract_experience_years(text):
    """
    Extract years of professional experience from resume text.

    Examples detected:

        "2 years of experience"
        "3+ years experience"
        "5 years in software development"

    Returns:
        float/int value or None
    """

    if not text:
        return None

    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+of\s+experience",
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+experience",
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+in\s+",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            value = float(match.group(1))

            if value.is_integer():
                return int(value)

            return value

    return None


# ============================================================
# ROLE DETECTION
# ============================================================

def extract_roles(text):
    """
    Detect predefined professional roles from resume text.
    """

    if not text:
        return []

    found_roles = []

    for role in ROLE_LIBRARY:

        pattern = _build_skill_pattern(role)

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):
            found_roles.append(role)

    return found_roles


# ============================================================
# EDUCATION PARSING
# ============================================================

DEGREE_PATTERNS = [
    r"\bM\.?\s*Sc\.?\b",
    r"\bB\.?\s*Sc\.?\b",
    r"\bM\.?\s*Tech\.?\b",
    r"\bB\.?\s*Tech\.?\b",
    r"\bM\.?\s*E\.?\b",
    r"\bB\.?\s*E\.?\b",
    r"\bMCA\b",
    r"\bBCA\b",
    r"\bMBA\b",
    r"\bPh\.?\s*D\.?\b",
    r"\bMaster(?:'s)?\s+of\b",
    r"\bBachelor(?:'s)?\s+of\b",
    r"\bDiploma\b",
]


def extract_education(text):
    """
    Extract education-related lines from resume text.

    This is a rule-based fundamentals implementation.
    """

    if not text:
        return []

    education_lines = []

    for line in text.splitlines():

        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        for pattern in DEGREE_PATTERNS:

            if re.search(
                pattern,
                cleaned_line,
                re.IGNORECASE
            ):
                education_lines.append(
                    cleaned_line
                )
                break

    return education_lines


# ============================================================
# GENERAL PATTERN EXTRACTION
# ============================================================

def extract_email(text):
    """
    Extract the first email address.
    """

    if not text:
        return None

    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    match = re.search(
        pattern,
        text
    )

    if match:
        return match.group(0)

    return None


def extract_phone(text):
    """
    Extract a likely phone number from resume text.
    """

    if not text:
        return None

    patterns = [
        r"\+?\d[\d\s().-]{8,}\d",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:
            phone = match.group(0).strip()

            return phone

    return None


# ============================================================
# RESUME ANALYSIS
# ============================================================

def analyze_resume_text(text):
    """
    Main NLP function.

    Converts cleaned resume text into structured data.
    """

    if not text:
        return {
            "tokens": [],
            "keywords": [],
            "skills": [],
            "experience": {
                "years": None,
                "roles": [],
            },
            "education": [],
            "contact": {
                "email": None,
                "phone": None,
            },
        }

    tokens = tokenize_text(text)

    skills = extract_skills(text)

    roles = extract_roles(text)

    education = extract_education(text)

    experience_years = extract_experience_years(text)

    keywords = extract_keywords(
        text,
        skills
    )

    email = extract_email(text)

    phone = extract_phone(text)

    return {
        "tokens": tokens,

        "keywords": keywords,

        "skills": skills,

        "experience": {
            "years": experience_years,
            "roles": roles,
        },

        "education": education,

        "contact": {
            "email": email,
            "phone": phone,
        },
    }