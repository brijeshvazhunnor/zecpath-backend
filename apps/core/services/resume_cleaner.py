import re


def clean_resume_text(text):
    """
    Clean and normalize extracted resume text.

    Operations:
    - Remove null characters
    - Normalize line endings
    - Remove excessive spaces
    - Remove excessive blank lines
    - Clean spaces around punctuation
    - Preserve meaningful line structure
    """

    if not text:
        return ""

    # Remove null characters and other problematic control characters
    text = text.replace("\x00", "")

    # Normalize Windows/Mac line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove trailing spaces from each line
    lines = []

    for line in text.split("\n"):
        line = line.strip()

        # Replace multiple spaces/tabs with a single space
        line = re.sub(r"[ \t]+", " ", line)

        if line:
            lines.append(line)

    # Join lines
    text = "\n".join(lines)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Clean spaces before punctuation
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    # Normalize multiple spaces again
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


def normalize_resume_text(text):
    """
    Additional normalization layer.

    Keeps the resume human-readable while making the text
    more consistent for future NLP/AI processing.
    """

    if not text:
        return ""

    text = clean_resume_text(text)

    # Normalize common bullet characters
    text = text.replace("•", "-")
    text = text.replace("●", "-")
    text = text.replace("▪", "-")
    text = text.replace("◦", "-")

    # Remove repeated hyphens used as decorative separators
    text = re.sub(r"-{3,}", "-", text)

    return text.strip()