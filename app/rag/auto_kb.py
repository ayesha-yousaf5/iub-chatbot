import json
import os
import re
from functools import lru_cache
from difflib import SequenceMatcher

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")
CLEANED_DOCUMENTS_PATH = os.path.join(PROCESSED_DIR, "cleaned_documents.json")

PROGRAM_PREFIXES = (
    "BS", "MS", "MPhil", "M.Phil", "PhD", "Ph.D", "MSc", "MBA", "MFA",
    "LLM", "Pharm-D", "BSc", "B.Ed", "ADP", "Diploma"
)

STOP_SECTION_PREFIXES = (
    "Faculty of ",
    "Rahim Yar Khan Campus",
    "Bahawalnagar Campus",
    "GENERAL INSTRUCTIONS",
    "General Instructions",
)


def normalize(text: str) -> str:
    text = str(text or "").lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


@lru_cache(maxsize=1)
def load_documents():
    if not os.path.exists(CLEANED_DOCUMENTS_PATH):
        raise FileNotFoundError(
            f"cleaned_documents.json not found at {CLEANED_DOCUMENTS_PATH}. Run: python -m rag.ingest"
        )

    with open(CLEANED_DOCUMENTS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def find_document(source_name_contains: str):
    needle = normalize(source_name_contains)
    for doc in load_documents():
        if needle in normalize(doc.get("source", "")):
            return doc
    return None


def source_list_for_category(category: str):
    docs = []
    for doc in load_documents():
        if normalize(doc.get("category")) == normalize(category):
            docs.append(doc)
    return docs


@lru_cache(maxsize=1)
def get_admission_procedure():
    doc = find_document("how to apply for admission")
    if not doc:
        return None
    return {
        "title": "Admission Procedure",
        "text": doc.get("text", "").strip(),
        "source": doc.get("source"),
        "category": doc.get("category"),
    }


@lru_cache(maxsize=1)
def get_faculties():
    doc = find_document("faculties with department")
    if not doc:
        return {}

    lines = [line.strip() for line in doc.get("text", "").splitlines() if line.strip()]
    faculties = {}
    current_faculty = None
    current_unit = None

    def is_program_line(line: str) -> bool:
        compact = line.strip()
        return any(compact.startswith(prefix) for prefix in PROGRAM_PREFIXES)

    for line in lines:
        if line.startswith("[PAGE") or line.startswith("https://"):
            continue

        if line.startswith("Faculty of "):
            current_faculty = line.strip()
            current_unit = None
            faculties.setdefault(current_faculty, {"units": {}, "source": doc.get("source"), "category": doc.get("category")})
            continue

        if current_faculty is None:
            continue

        if any(line.startswith(prefix) for prefix in STOP_SECTION_PREFIXES) and not line.startswith("Faculty of "):
            current_faculty = None
            current_unit = None
            continue

        if is_program_line(line):
            if current_unit:
                faculties[current_faculty]["units"].setdefault(current_unit, []).append(line)
            continue

        # Otherwise it is a department/institute/unit line.
        current_unit = line
        faculties[current_faculty]["units"].setdefault(current_unit, [])

    return faculties


def find_faculty(query: str):
    faculties = get_faculties()
    if not faculties:
        return None, None

    q = normalize(query)
    best_name = None
    best_score = 0

    for faculty_name in faculties:
        fn = normalize(faculty_name)
        short = fn.replace("faculty of", "").strip()

        if fn in q or short in q:
            return faculty_name, faculties[faculty_name]

        score = max(similarity(q, faculty_name), similarity(q.replace("faculty", ""), short))
        if score > best_score:
            best_score = score
            best_name = faculty_name

    if best_score >= 0.62:
        return best_name, faculties[best_name]

    return None, None


@lru_cache(maxsize=1)
def get_scholarship_docs():
    return source_list_for_category("scholarships")


def find_scholarship(query: str):
    docs = get_scholarship_docs()
    if not docs:
        return None
    q = normalize(query)
    best_doc = None
    best_score = 0

    for doc in docs:
        name = doc.get("source", "")
        clean_name = normalize(name.replace(".docx", ""))
        if clean_name and clean_name in q:
            return doc
        # Match individual scholarship keywords such as beef, peef, diya, ehsaas.
        for token in clean_name.split():
            if len(token) >= 4 and token in q:
                return doc
        score = similarity(q, clean_name)
        if score > best_score:
            best_score = score
            best_doc = doc

    if best_score >= 0.45:
        return best_doc
    return None


def list_scholarships():
    names = []
    for doc in get_scholarship_docs():
        name = doc.get("source", "").replace(".docx", "")
        names.append(name)
    return names


@lru_cache(maxsize=1)
def get_fee_text():
    doc = find_document("Revised fee")
    if not doc:
        return None
    return doc


def search_fee_text(program_query: str):
    """
    Data-driven fee search. It does not store manual fee facts.
    It searches the official Revised fee text and returns matching sentences.
    """
    doc = get_fee_text()
    if not doc:
        return None

    text = doc.get("text", "")
    q = normalize(program_query)
    if not q:
        return None

    sentences = re.split(r"(?<=[.!?])\s+", text)
    scored = []

    q_tokens = [t for t in q.split() if len(t) > 2]

    for sent in sentences:
        ns = normalize(sent)
        if "fee" not in ns and "tuition" not in ns and "dues" not in ns:
            continue

        overlap = sum(1 for token in q_tokens if token in ns)
        fuzzy = similarity(q, ns[:160])
        score = overlap + fuzzy

        if score >= 1.35:
            scored.append((score, sent.strip()))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return None

    selected = []
    seen = set()
    for _, sent in scored[:4]:
        key = normalize(sent[:120])
        if key not in seen:
            seen.add(key)
            selected.append(sent)

    return {
        "text": "\n".join(selected),
        "source": doc.get("source"),
        "category": doc.get("category"),
    }


@lru_cache(maxsize=1)
def get_hostel_text():
    doc = find_document("residential and hostel facilities")
    if not doc:
        return None
    return doc
