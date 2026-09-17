from rag.query_processor import expand_abbreviations


PROGRAM_TERMS = {
    "computer science": [
        "computer science",
        "bs computer science",
        "bs cs",
        "BSCS",
        "bscs",
        "department of computer science",
    ],
    "artificial intelligence": [
        "artificial intelligence",
        "bs artificial intelligence",
        "bs ai",
        "BSAI",
        "bsai",
    ],
    "software engineering": [
        "software engineering",
        "bs software engineering",
        "bs se",
        "BSSE",
        "bsse"
    ],
    "data science": [
        "data science",
        "bs data science",
        "bs ds",
    ],
    "information technology": [
        "information technology",
        "bs information technology",
        "bs it",
    ],
}


ROLE_WORDS = [
    "who is",
    "director",
    "head",
    "incharge",
    "deputy",
    "registrar",
    "treasurer",
    "controller",
    "vice chancellor",
    "vc",
    "chairman",
    "coordinator",
    "focal person",
]

ADMISSION_WORDS = [
    "admission",
    "criteria",
    "eligibility",
    "requirement",
    "requirements",
    "apply",
    "merit",
    "fee",
    "fees",
]


def is_role_question(question: str):
    q = question.lower()

    for word in ROLE_WORDS:
        if word in q:
            return True

    return False


def is_program_admission_question(question: str):
    q = question.lower()

    for word in ADMISSION_WORDS:
        if word in q:
            return True

    return False


def detect_program(question: str):
    q = expand_abbreviations(question).lower()

    for program, terms in PROGRAM_TERMS.items():
        for term in terms:
            if term in q:
                return program

    return None


def validate_context_for_question(question: str, retrieved_docs):
    """
    Validate only specific program admission/fee/criteria questions.
    Do not validate role/designation questions like:
    who is director of IT?
    """

    # Do not block role/person/designation questions
    if is_role_question(question):
        return True

    # Validate only admission/criteria/fee type program questions
    if not is_program_admission_question(question):
        return True

    program = detect_program(question)

    if not program:
        return True

    program_terms = PROGRAM_TERMS.get(program, [])

    combined_context = " ".join(
        doc["content"].lower()
        for doc in retrieved_docs
    )

    for term in program_terms:
        if term in combined_context:
            return True

    return False