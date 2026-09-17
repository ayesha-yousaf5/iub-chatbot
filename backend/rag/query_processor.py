import re


ABBREVIATIONS = {
    # University administration
    "vc": "vice chancellor",
    "v.c": "vice chancellor",
    "v c": "vice chancellor",
    "doit": "directorate of information technology",

    # Computer / IT fields
    "cs": "computer science",
    "se": "software engineering",
    "ai": "artificial intelligence",
    "ds": "data science",
    "ict": "information and communication technology",

    # Degree programs
    "bs": "bachelor of science",
    "bsc": "bachelor of science",
    "ms": "master of science",
    "mphil": "master of philosophy",
    "phd": "doctor of philosophy",
    "adp": "associate degree program",
    "llb": "bachelor of laws",
    "bba": "bachelor of business administration",
    "mba": "master of business administration",

    # Admission/tests
    "lat": "law admission test",
    "hec": "higher education commission",
    "nts": "national testing service",
}


def clean_query_text(question: str) -> str:
    question = question.strip()
    question = re.sub(r"\s+", " ", question)
    return question


def expand_abbreviations(question: str) -> str:
    original_question = clean_query_text(question)
    expanded_question = original_question.lower()

    for short_form, full_form in ABBREVIATIONS.items():
        pattern = r"\b" + re.escape(short_form.lower()) + r"\b"
        expanded_question = re.sub(pattern, full_form, expanded_question)

    extra_terms = []

    q = expanded_question.lower()

    # Program aliases
    if "computer science" in q:
        extra_terms.extend([
            "CS",
            "Computer Science",
            "BS CS",
            "BS Computer Science",
        ])

    if "artificial intelligence" in q:
        extra_terms.extend([
            "AI",
            "Artificial Intelligence",
            "BS AI",
            "BS Artificial Intelligence",
        ])

    if "software engineering" in q:
        extra_terms.extend([
            "SE",
            "Software Engineering",
            "BS SE",
            "BS Software Engineering",
        ])

    if "data science" in q:
        extra_terms.extend([
            "DS",
            "Data Science",
            "BS DS",
            "BS Data Science",
        ])

    # DoIT aliases only when DoIT/IT directorate is clearly asked
    if (
        "doit" in original_question.lower()
        or "directorate of it" in original_question.lower()
        or "directorate of information technology" in q
        or "director of it" in original_question.lower()
        or "director it" in original_question.lower()
    ):
        extra_terms.extend([
            "Directorate of Information Technology",
            "DoIT",
            "Director IT",
            "Information Technology Directorate",
        ])

    final_query = f"{original_question} {expanded_question} {' '.join(set(extra_terms))}"

    return final_query.strip()