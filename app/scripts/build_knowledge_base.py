import json
import os
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")
CLEANED_DOCS_PATH = os.path.join(PROCESSED_DIR, "cleaned_documents.json")
KB_DIR = os.path.join(BASE_DIR, "knowledge_base")

DEGREE_PREFIXES = (
    "BS", "BSc", "B.Sc", "MS", "MSc", "M.Sc", "MPhil", "M.Phil", "PhD", "Ph.D",
    "MBA", "BBA", "LLB", "LLM", "DVM", "MBBS", "BDS", "Pharm-D", "Pharm D",
    "Doctor", "Diploma", "Certificate", "MFA", "Generic"
)

STOP_LINES = {
    "https://eportal.iub.edu.pk", "apply online", "the islamia university of bahawalpur, pakistan",
    "admissions open", "mphil/ms/msc (hons)/mba/llm & phd", "admissions-spring semester, 2026"
}


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_documents():
    if not os.path.exists(CLEANED_DOCS_PATH):
        raise FileNotFoundError(f"cleaned_documents.json not found: {CLEANED_DOCS_PATH}")
    with open(CLEANED_DOCS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(name: str, data):
    ensure_dir(KB_DIR)
    path = os.path.join(KB_DIR, name)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    print(f"Saved {path}")


def normalize(text: str) -> str:
    text = str(text or "").lower()
    replacements = {
        "&": " and ",
        "v.c": "vc",
        "v c": "vc",
        "b.s.": "bs",
        "b s": "bs",
        "c.s.": "cs",
        "c s": "cs",
        "ph.d": "phd",
        "m.phil": "mphil",
        "pharm d": "pharm-d",
        "pharm.d": "pharm-d",
        "phisio": "physio",
        "physio therapist": "physical therapy",
        "phisiotherapist": "physical therapy",
        "baghdad ul jadeed": "baghdad-ul-jadeed",
        "baghdad-ul-jaded": "baghdad-ul-jadeed",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^a-z0-9\s\-/]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_line(line: str) -> str:
    line = re.sub(r"\s+", " ", str(line or "")).strip()
    return line.strip(" |\t")


def title_from_source(source: str) -> str:
    return os.path.splitext(source)[0].strip()


def get_doc(docs, source_name: str):
    for doc in docs:
        if doc.get("source", "").lower() == source_name.lower():
            return doc
    return None


def is_degree_line(line: str) -> bool:
    line = clean_line(line)
    if not line:
        return False
    low = line.lower()
    if low in STOP_LINES:
        return False
    return any(low.startswith(prefix.lower()) for prefix in DEGREE_PREFIXES)


def looks_like_unit(line: str) -> bool:
    line = clean_line(line)
    if not line or is_degree_line(line):
        return False
    low = line.lower()
    if low.startswith("faculty of"):
        return False
    if low.startswith("[page") or low in STOP_LINES:
        return False
    if len(line) > 90:
        return False
    return True


def build_faculties(docs):
    doc = get_doc(docs, "faculties with department.pdf")
    if not doc:
        return []
    lines = [clean_line(x) for x in doc.get("text", "").splitlines()]
    lines = [x for x in lines if x]
    faculties = []
    current = None
    current_unit = None

    for line in lines:
        low = line.lower()
        if low.startswith("faculty of"):
            if current:
                faculties.append(current)
            current = {
                "faculty": line,
                "faculty_norm": normalize(line),
                "units": [],
                "source": doc.get("source"),
                "category": doc.get("category"),
            }
            current_unit = None
            continue

        if not current:
            continue

        if is_degree_line(line):
            if current_unit is None:
                current_unit = {"name": "Programs", "name_norm": normalize("Programs"), "programs": []}
                current["units"].append(current_unit)
            if line not in current_unit["programs"]:
                current_unit["programs"].append(line)
            continue

        if looks_like_unit(line):
            current_unit = {"name": line, "name_norm": normalize(line), "programs": []}
            current["units"].append(current_unit)

    if current:
        faculties.append(current)

    return faculties


def build_fees(docs):
    doc = get_doc(docs, "Revised fee.docx")
    if not doc:
        return []
    text = doc.get("text", "")
    pattern = re.compile(
        r"(?P<program>[A-Z][A-Za-z0-9 .,&/\-()]+?)\s*"
        r"\((?P<group>Group-[AB]|Evening|Morning)\)\s*"
        r"(?:with|has)\s+tuition fee\s+(?P<tuition>\d+),\s*"
        r"other dues\s+(?:are\s+)?(?P<other_dues>\d+),\s*"
        r"total fee\s*(?:for)?\s*1st semester\s*(?:is\s*)?(?P<first_semester>\d+)\s+and\s+"
        r"total fee\s*(?:for)?\s*2nd\s*&\s*other semesters\s*(?:is\s*)?(?P<other_semesters>\d+)",
        flags=re.IGNORECASE,
    )
    rows = []
    for match in pattern.finditer(text):
        program = clean_line(match.group("program"))[-140:]
        program = re.sub(
            r"^.*?\b((?:BS|BSc|B\.Sc|M\.Phil/MS|MPhil/MS|MPhil|MS|MSc|M\.Sc|Ph\.D|PhD|Diploma|LLB|BBA|MBA|Pharm-D|Pharm D|DVM|Doctor|Generic|BDS|MBBS|Certificate|MFA)\b)",
            r"\1",
            program,
            flags=re.IGNORECASE,
        )
        program = clean_line(program)
        rows.append({
            "program": program,
            "program_norm": normalize(program),
            "acronyms": extract_acronyms(program),
            "group": match.group("group"),
            "tuition_fee": int(match.group("tuition")),
            "other_dues": int(match.group("other_dues")),
            "total_1st_semester": int(match.group("first_semester")),
            "total_other_semesters": int(match.group("other_semesters")),
            "source": doc.get("source"),
            "category": doc.get("category"),
        })
    unique, seen = [], set()
    for row in rows:
        key = (row["program_norm"], row["group"], row["tuition_fee"], row["total_1st_semester"])
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique


def extract_acronyms(text: str):
    acronyms = set()
    for item in re.findall(r"\(([A-Za-z][A-Za-z\-]{1,10})\)", text or ""):
        acronyms.add(normalize(item))
    words = re.findall(r"\b[A-Z]{2,}\b", text or "")
    for w in words:
        acronyms.add(normalize(w))
    return sorted(acronyms)


def build_admissions(docs):
    admissions = {"procedure": None, "program_criteria": []}
    procedure_doc = get_doc(docs, "how to apply for admission.docx")
    if procedure_doc:
        steps = []
        for line in procedure_doc.get("text", "").splitlines():
            line = clean_line(line)
            if line:
                steps.append(line)
        admissions["procedure"] = {
            "title": "Admission Procedure",
            "steps": steps,
            "source": procedure_doc.get("source"),
            "category": procedure_doc.get("category"),
        }

    criteria_doc = get_doc(docs, "Admissions_Criteria_Paragraphsupdated.docx")
    if criteria_doc:
        text = criteria_doc.get("text", "")
        parts = [clean_line(x) for x in re.split(r"(?<=\.)\s+|\n+", text) if clean_line(x)]
        for part in parts:
            if any(word in part.lower() for word in ["offers", "requires", "criteria", "merit", "eligible", "eligibility"]):
                admissions["program_criteria"].append({
                    "text": part,
                    "text_norm": normalize(part),
                    "source": criteria_doc.get("source"),
                    "category": criteria_doc.get("category"),
                })
    return admissions


def build_people(docs):
    people = []
    patterns = [
        r"(?P<name>[A-Z][A-Za-z .\'-]{2,80}?)\s+serves as\s+(?P<designation>[^.\n]+)",
        r"(?P<name>[A-Z][A-Za-z .\'-]{2,80}?)\s+works as\s+(?P<designation>[^.\n]+)",
        r"(?P<name>[A-Z][A-Za-z .\'-]{2,80}?)\s+is\s+(?:the\s+)?(?P<designation>Vice Chancellor|Dean|Director|Chairman|Chairperson|Registrar|Treasurer|Controller|Chief Security Officer[^.\n]*)",
        r"(?P<designation>Vice Chancellor(?:\s+of\s+the\s+IUB)?)\s+is\s+(?P<name>[A-Z][A-Za-z .\'-]{2,80})",
    ]
    for doc in docs:
        if doc.get("category") != "faculty and departments":
            continue
        text = doc.get("text", "")
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                name = clean_line(match.group("name"))
                designation = clean_line(match.group("designation"))
                if not valid_person_name(name) or len(designation) > 160:
                    continue
                people.append({
                    "name": name,
                    "name_norm": normalize(name),
                    "designation": designation,
                    "designation_norm": normalize(designation),
                    "source": doc.get("source"),
                    "category": doc.get("category"),
                })
    unique, seen = [], set()
    for p in people:
        key = (p["name_norm"], p["designation_norm"], p["source"])
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def valid_person_name(name: str) -> bool:
    if not name:
        return False
    low = name.lower()
    bad_words = ["directorate", "university", "faculty", "department", "campus", "role", "contact", "qualifications", "leadership", "staff members"]
    if any(w in low for w in bad_words):
        return False
    words = name.split()
    return 2 <= len(words) <= 8


def build_simple_doc_list(docs, category: str):
    rows = []
    for doc in docs:
        if doc.get("category") == category:
            text = doc.get("text", "")
            preview = clean_line(re.sub(r"\s+", " ", text[:350]))
            rows.append({
                "name": title_from_source(doc.get("source", "")),
                "name_norm": normalize(title_from_source(doc.get("source", ""))),
                "source": doc.get("source"),
                "category": doc.get("category"),
                "preview": preview,
                "text": text,
            })
    return rows


def build_hostels(docs):
    doc = get_doc(docs, "residential and hostel facilities.docx")
    if not doc:
        return {"text": "", "source": None, "category": "hostels", "campus_sections": []}
    text = doc.get("text", "")
    campus_sections = []
    # Data-driven sentence extraction: no hostel names are hardcoded; all are pulled from the hostel document.
    sentences = [clean_line(x) for x in re.split(r"(?<=\.)\s+", text) if clean_line(x)]
    for sent in sentences:
        if "hostel" in sent.lower() or "hall" in sent.lower() or "campus" in sent.lower():
            campus_sections.append(sent)
    return {"text": text, "source": doc.get("source"), "category": doc.get("category"), "campus_sections": campus_sections}


def main():
    docs = load_documents()
    save_json("faculties.json", build_faculties(docs))
    save_json("fees.json", build_fees(docs))
    save_json("admissions.json", build_admissions(docs))
    save_json("people.json", build_people(docs))
    save_json("campuses.json", build_simple_doc_list(docs, "campuses"))
    save_json("scholarships.json", build_simple_doc_list(docs, "scholarships"))
    save_json("hostels.json", build_hostels(docs))
    print("Knowledge base generation completed.")


if __name__ == "__main__":
    main()
