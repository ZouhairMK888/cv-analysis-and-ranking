import re
from datetime import datetime

import spacy

nlp = spacy.load("en_core_web_sm")

MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


def extract_name(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:6]:
        if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+$", line):
            return line
    for ent in nlp(text).ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None


def extract_email(text):
    m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else None


def extract_phone(text):
    """
    Extract international phone numbers:
    +212, +33, +1, +44, etc.
    """
    match = re.search(
        r"(\+?\d{1,4}[\s\-\.]?\(?\d{1,4}\)?([\s\-\.]?\d{2,4}){2,4})", text
    )
    return match.group(0) if match else None


def extract_skills(text):
    """
    Extract skills from 'Skills' section or inline lists
    """
    skills = []

    text_lower = text.lower()

    # Case 1: skills section
    if "skills" in text_lower:
        lines = text.split("\n")
        capture = False

        for line in lines:
            if "skills" in line.lower():
                capture = True
                continue

            if capture:
                if line.strip() == "":
                    break

                # Split comma-separated skills
                parts = re.split(r",|•|-", line)
                for p in parts:
                    p = p.strip()
                    if len(p) > 2:
                        skills.append(p)

    # Case 2: fallback (common skills anywhere)
    COMMON_SKILLS = [
        "python",
        "java",
        "sql",
        "management",
        "leadership",
        "communication",
        "marketing",
        "design",
        "excel",
        "git",
        "AI",
        "machine learning",
        "NLP",
        "deep learning",
        "natural language processing",
    ]

    for skill in COMMON_SKILLS:
        if skill in text_lower and skill.capitalize() not in skills:
            skills.append(skill.capitalize())

    return list(set(skills))


CURRENT_YEAR = datetime.now().year


def extract_experience_years(text):
    """
    Count ONLY professional work experience.
    Ignore education, academic projects, certificates.
    Ignore internships < 6 months.
    """
    text_lower = text.lower()

    # Only look AFTER the experience section
    if "experience" in text_lower:
        text_lower = text_lower.split("experience", 1)[1]
    else:
        return 0  # no experience section → student

    # Remove education & academic sections if they appear later
    stop_words = ["education", "certificat", "projet", "academic"]
    for w in stop_words:
        if w in text_lower:
            text_lower = text_lower.split(w, 1)[0]

    matches = re.findall(
        r"(20\d{2})\s*(?:-|–|—|to)?\s*(present|current|20\d{2})", text_lower
    )

    total_years = 0

    for start, end in matches:
        start = int(start)
        end = CURRENT_YEAR if end in ["present", "current"] else int(end)

        duration = end - start

        # Ignore internships / very short experience
        if duration >= 1:
            total_years += duration

    return total_years
