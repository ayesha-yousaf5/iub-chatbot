import json
import os
import re
from functools import lru_cache
from typing import Dict, List, Optional


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")
CLEANED_DOCS_PATH = os.path.join(PROCESSED_DIR, "cleaned_documents.json")


PROGRAM_ALIASES = {
    "cs": "BS Computer Science",
    "computer science": "BS Computer Science",
    "bs cs": "BS Computer Science",
    "bs computer science": "BS Computer Science",
    "chemistry": "BS Chemistry",
    "bs chemistry": "BS Chemistry",
    "dpt": "Doctor of Physical Therapy (DPT) (5 Years Program)",
    "doctor of physical therapy": "Doctor of Physical Therapy (DPT) (5 Years Program)",
    "doctor of phisio therapist": "Doctor of Physical Therapy (DPT) (5 Years Program)",
    "doctor of physio therapy": "Doctor of Physical Therapy (DPT) (5 Years Program)",
    "physical therapy": "Doctor of Physical Therapy (DPT) (5 Years Program)",
    "pharm d": "Doctor of Pharmacy (Pharm-D) (5 Years Program)",
    "pharm-d": "Doctor of Pharmacy (Pharm-D) (5 Years Program)",
    "doctor of pharmacy": "Doctor of Pharmacy (Pharm-D) (5 Years Program)",
    "it": "BS Information Technology",
    "information technology": "BS Information Technology",
    "bs it": "BS Information Technology",
    "bs information technology": "BS Information Technology",
    "ai": "BS Artificial Intelligence",
    "artificial intelligence": "BS Artificial Intelligence",
    "bs ai": "BS Artificial Intelligence",
    "bs artificial intelligence": "BS Artificial Intelligence",
    "se": "BS Software Engineering",
    "software engineering": "BS Software Engineering",
    "bs se": "BS Software Engineering",
    "bs software engineering": "BS Software Engineering",
    "ds": "BS Data Science",
    "data science": "BS Data Science",
    "bs ds": "BS Data Science",
    "bs data science": "BS Data Science",
    "electrical engineering": "BSc Electrical Engineering",
    "bsc electrical engineering": "BSc Electrical Engineering",
    "electronic engineering": "BSc Electronic Engineering",
    "bsc electronic engineering": "BSc Electronic Engineering",
}


FACULTY_DATA = {
    "Faculty of Arts & Languages": {
        "aliases": ["faculty of arts and languages", "faculty of arts & languages", "faculty of arts and language", "faculty of arts language"],
        "units": {
            "English Linguistics": ["MPhil English Linguistics", "PhD English Linguistics"],
            "English Literature": ["MPhil English Literature", "PhD English Literature"],
            "History": ["MPhil History (E/W)", "PhD History (E/W)"],
            "Iqbal Studies": ["MPhil Iqbal Studies", "PhD Iqbal Studies"],
            "Siraiki": ["MPhil Siraiki", "PhD Siraiki"],
            "Persian": ["MPhil Persian (E/W)", "PhD Persian"],
            "Pakistan Studies": ["MPhil Pakistan Studies (E/W)", "PhD Pakistan Studies (E/W)"],
            "Urdu & Iqbaliat": ["MPhil Urdu & Iqbaliat", "PhD Urdu & Iqbaliat"],
            "University College of Arts and Design": ["MFA in Visual Arts"],
        },
    },
    "Faculty of Agriculture and Environmental Sciences": {
        "aliases": ["faculty of agriculture", "faculty of agriculture and environmental sciences", "agriculture and environmental sciences"],
        "units": {
            "Agronomy": ["MSc (Hons) Agronomy", "PhD Agronomy"],
            "Entomology": ["MSc (Hons) Entomology", "PhD Entomology"],
            "Institute of Forest Sciences": ["MSc (Hons) Forestry", "MPhil Forestry", "MPhil Wildlife", "PhD Forestry", "PhD Wildlife"],
            "Food Science & Technology": ["MSc (Hons) Food Science & Technology", "PhD Food Science & Technology"],
            "Horticulture Sciences": ["MSc (Hons) Horticulture Sciences", "PhD Horticulture Sciences"],
            "Plant Breeding and Genetics": ["MSc (Hons) Plant Breeding and Genetics", "PhD Plant Breeding and Genetics"],
            "Plant Pathology": ["MSc (Hons) Plant Pathology", "PhD Plant Pathology"],
            "Soil Science": ["MSc (Hons) Soil Science", "PhD Soil Science"],
            "Institute of Agro-Industry & Environment": ["MS Environmental Sciences (E/W)", "PhD Environmental Science"],
            "Agriculture Extension": ["MSc (Hons) Agriculture - Agricultural Extension Education"],
        },
    },
    "Faculty of Chemical & Biological Sciences": {
        "aliases": ["faculty of chemical and biological sciences", "faculty of chemical & biological sciences", "chemical biological sciences"],
        "units": {
            "Institute of Chemistry": ["MPhil Chemistry", "PhD Chemistry"],
            "Zoology": ["MS Zoology", "PhD Zoology"],
            "Botany": ["MS Botany", "PhD Botany"],
            "Institute of Biochemistry, Biotechnology & Bioinformatics": ["MS Biochemistry", "MS Molecular Biology", "PhD Molecular Biology", "PhD Biochemistry", "MS Biotechnology", "PhD Biotechnology", "MS Bioinformatics"],
        },
    },
    "Faculty of Computing": {
        "aliases": ["faculty of computing", "computing faculty"],
        "units": {
            "Artificial Intelligence": ["MS Artificial Intelligence", "PhD Artificial Intelligence"],
            "Computer Science": ["MS Computer Science (E/W)", "PhD Computer Science"],
            "Data Science": ["MS Data Science"],
            "Information Security": ["MS Information Security (E/W)"],
            "Information Technology": ["MS Information Technology", "MS Information Technology Project Management", "PhD Information Technology"],
            "Software Engineering": ["MS Software Engineering"],
            "Statistics": ["MPhil Statistics (E/W)", "PhD Statistics"],
        },
    },
    "Faculty of Education": {
        "aliases": ["faculty of education", "education faculty"],
        "units": {
            "Education": ["MPhil Education (E/W)", "PhD Education (E/W)"],
            "Educational Training": ["MPhil Educational Training (E/W)", "PhD Educational Training"],
            "Educational Leadership & Management": ["MPhil Educational Leadership & Management (E/W)", "PhD Educational Leadership & Management (E/W)"],
            "Language Education": ["MPhil English Language Teaching", "PhD English Language Teaching"],
            "Special Education": ["MPhil Special Education (E/W)"],
            "Physical Education and Sports Sciences": ["MPhil Physical Education & Sports Sciences"],
        },
    },
    "Faculty of Engineering and Technology": {
        "aliases": ["faculty of engineering and technology", "faculty of engineering", "engineering and technology"],
        "units": {
            "Computer Systems Engineering": ["MSc Computer System Engineering"],
            "Electrical Power Engineering": ["MSc Electrical Power Engineering", "PhD Electrical Engineering"],
            "Information & Communication Engineering": ["MSc Electrical Engineering (Communication & Signal Processing)", "MSc Biomedical Engineering"],
            "Electronics Engineering": ["MSc Advanced Electronics & Control System Engineering"],
            "Civil Engineering": ["MS Civil Engineering", "PhD Civil Engineering"],
            "Advanced Electronic & Control System": ["MSc Advanced Electronic & Control System Engineering"],
        },
    },
    "Faculty of Islamic Learning": {
        "aliases": ["faculty of islamic learning", "islamic learning"],
        "units": {
            "Arabic": ["MPhil Arabic", "PhD Arabic"],
            "Fiqh & Shariah": ["MPhil Islamic Studies with Specialization in Fiqh & Shariah", "PhD Islamic Studies with Specialization in Fiqh and Sharia"],
            "Hadith": ["PhD Islamic Studies with specialization in Hadith & Seerah"],
            "Islamic Studies": ["MPhil Islamic Studies", "PhD Islamic Studies"],
            "Quranic Studies": ["MPhil Islamic Studies with Specialization in Quran wa Tafseer", "PhD Islamic Studies with Specialization in Quran & Tafseer"],
            "World Religions & Interfaith Harmony": ["MPhil Islamic Studies with Specialization in World Religions & Interfaith Harmony", "PhD Islamic Studies with Specialization in World Religions and Interfaith Harmony"],
        },
    },
    "Faculty of Management Sciences and Commerce": {
        "aliases": ["faculty of management sciences and commerce", "management sciences and commerce", "faculty of management"],
        "units": {
            "Commerce": ["MPhil Commerce", "MS Banking and Finance", "PhD Commerce"],
            "Institute of Business Management and Administrative Sciences": ["MS Management Sciences (E/W)", "MBA for Non-Business Graduates (E/W)", "MBA (E/W)", "PhD Management Sciences (E/W)"],
            "Administrative Sciences": ["MS Administrative and Management Sciences (E/W)"],
            "Finance and Investment": ["MS Finance & Investment (E/W)"],
            "Project and Operations Management": ["MS Operations & Supply Chain Management (E/W)", "MS Project Management (E/W)", "MBA Supply Chain Management (E/W)"],
            "Islamic & Conventional Banking": ["MS Islamic Banking & Finance (E/W)"],
            "Leadership & Management": ["MS Leadership & Management (E/W)", "PhD Leadership & Management (E/W)"],
            "Tourism & Hospitality Management": ["MBA Tourism & Hospitality Management (E/W)"],
        },
    },
    "Faculty of Medicine and Allied Health Sciences": {
        "aliases": ["faculty of medicine and allied health sciences", "medicine and allied health", "faculty of medicine"],
        "units": {
            "Sir Sadiq Muhammad Khan Abbasi Post Graduate Medical College": ["MPhil Pharmacology", "MPhil Physiology"],
            "University College of Conventional Medicine": ["MPhil Eastern Medicine", "MPhil Phytomedicine", "PhD Eastern Medicine", "PhD Phytomedicine"],
            "University College of Nursing": ["MS Nursing (Morning Program)"],
        },
    },
    "Faculty of Pharmacy": {
        "aliases": ["faculty of pharmacy", "pharmacy faculty"],
        "units": {
            "Pharmaceutics": ["MPhil Pharmaceutics", "PhD Pharmaceutics"],
            "Pharmaceutical Chemistry": ["MPhil Pharmaceutical Chemistry", "PhD Pharmaceutical Chemistry"],
            "Pharmacology": ["MPhil Pharmacology", "PhD Pharmacology"],
            "Pharmacy Practice": ["MPhil Pharmacy Practice", "PhD Pharmacy Practice"],
            "Pharmacognosy": ["MPhil Pharmacognosy", "PhD Pharmacognosy"],
        },
    },
    "Faculty of Physical and Mathematical Sciences": {
        "aliases": ["faculty of physical and mathematical sciences", "physical and mathematical sciences"],
        "units": {
            "Mathematics": ["MPhil Mathematics", "PhD Mathematics"],
            "Geography": ["MPhil Geography", "PhD Geography"],
            "Institute of Physics": ["MPhil Physics", "PhD Physics"],
        },
    },
    "Faculty of Social Sciences": {
        "aliases": ["faculty of social sciences", "social sciences faculty"],
        "units": {
            "Applied Psychology": ["MPhil Applied Psychology (E/W)", "PhD Applied Psychology"],
            "Economics": ["MPhil Economics (E/W)", "PhD Economics"],
            "Gender Studies": ["MPhil Gender Studies (E/W)"],
            "International Relations": ["MPhil International Relations", "MPhil Defense & Diplomatic Studies", "PhD International Relations"],
            "Information Management": ["MPhil Information Management", "PhD Information Management"],
            "Media & Communication Studies": ["MPhil Media Studies", "PhD Media Studies"],
            "Political Science": ["MPhil Political Science", "PhD Political Science"],
            "Public Administration": ["MS Public Administration (E/W)"],
            "Social Work": ["MPhil Social Work (E/W)", "PhD Social Work"],
        },
    },
    "Faculty of Veterinary and Animal Sciences": {
        "aliases": ["faculty of veterinary and animal sciences", "veterinary and animal sciences"],
        "units": {
            "Anatomy & Histology": ["MPhil Anatomy & Histology"],
            "Animal Nutrition": ["MPhil Animal Nutrition"],
            "Animal Breeding & Genetics": ["MPhil Animal Breeding & Genetics"],
            "Livestock Management": ["MPhil Livestock Management"],
            "Microbiology": ["MPhil Microbiology"],
            "Parasitology": ["MPhil Parasitology"],
            "Physiology": ["MPhil Physiology"],
            "Pathology": ["MPhil Pathology"],
            "Poultry Science": ["MPhil Poultry Science"],
            "Theriogenology": ["MPhil Theriogenology"],
            "Veterinary Clinical Medicine & Surgery": ["MPhil Veterinary Clinical Medicine & Surgery"],
        },
    },
}

HOSTEL_CAMPUS_DATA = {
    "abbasia": {
        "campus": "Abbasia Campus",
        "items": ["Rabia Hall for girls", "Abu Bakar Hall for boys"],
    },
    "baghdad": {
        "campus": "Baghdad-ul-Jadeed Campus",
        "items": [
            "Fatima-tuz-Zahra Hall for girls",
            "Ayesha Siddiqa Hall for girls",
            "Khadija-tul-Kubra Hall for girls",
            "Amna Hall for girls",
            "Zainab Hall for girls",
            "Halima Hall for girls",
            "Umar Hall for boys",
            "Ali Hall for boys",
            "Ahmad Hall for boys",
            "Usman Hall for boys",
        ],
    },
    "bj": {
        "campus": "Baghdad-ul-Jadeed Campus",
        "items": [
            "Fatima-tuz-Zahra Hall for girls", "Ayesha Siddiqa Hall for girls", "Khadija-tul-Kubra Hall for girls",
            "Amna Hall for girls", "Zainab Hall for girls", "Halima Hall for girls", "Umar Hall for boys", "Ali Hall for boys", "Ahmad Hall for boys", "Usman Hall for boys",
        ],
    },
    "bahawalnagar": {
        "campus": "Bahawalnagar Campus",
        "items": ["Ayesha Hall for girls", "Abu Bakar Hall for boys"],
    },
    "ryk": {
        "campus": "Rahim Yar Khan Campus",
        "items": ["Ayesha Hall for girls", "Iqbal Hall for boys"],
    },
    "rahim yar khan": {
        "campus": "Rahim Yar Khan Campus",
        "items": ["Ayesha Hall for girls", "Iqbal Hall for boys"],
    },
}


def normalize(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    replacements = {
        "v.c": "vc", "v c": "vc", "b.s.": "bs", "b s": "bs", "c.s.": "cs", "c s": "cs",
        "ph.d": "phd", "m.phil": "mphil", "doit": "directorate of information technology",
        "director of it": "director it", "director of information technology": "director it",
        "physio therapist": "physical therapy", "phisio therapist": "physical therapy", "phisiotherapist": "physical therapy",
        "baghdad ul jadeed": "baghdad", "baghdad-ul-jadeed": "baghdad", "bj campus": "bj",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^a-z0-9\s&\-/.]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_cleaned_documents() -> List[Dict]:
    if not os.path.exists(CLEANED_DOCS_PATH):
        return []
    with open(CLEANED_DOCS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def get_doc_text(source_name: str) -> str:
    source_name = source_name.lower()
    for doc in load_cleaned_documents():
        if doc.get("source", "").lower() == source_name:
            return doc.get("text", "")
    return ""


def get_docs_by_category(category: str) -> List[Dict]:
    return [doc for doc in load_cleaned_documents() if doc.get("category", "").lower() == category.lower()]


def clean_program_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    return name.strip(" .,:;")


def title_program(program: str) -> str:
    program = clean_program_name(program)
    replacements = {"Bs ": "BS ", "Bsc ": "BSc ", "Mphil ": "MPhil ", "Ms ": "MS ", "Phd ": "PhD ", "Bba ": "BBA ", "Llb ": "LLB ", "Dvm": "DVM"}
    program = program.title()
    for old, new in replacements.items():
        program = program.replace(old, new)
    return program


def detect_group(question: str) -> Optional[str]:
    q = normalize(question)
    if "group a" in q or "group-a" in q:
        return "Group-A"
    if "group b" in q or "group-b" in q:
        return "Group-B"
    return None


@lru_cache(maxsize=1)
def build_fee_index() -> List[Dict]:
    text = get_doc_text("Revised fee.docx")
    fees = []
    segments = re.split(r"(?<=[.])\s+|\|", text)
    pattern = re.compile(
        r"(?P<program>[A-Z][A-Za-z0-9 .,&/\-()]+?)\s*"
        r"\((?P<group>Group-[AB]|Evening|Morning)\)\s*"
        r"(?:with|has)\s+tuition fee\s+(?P<tuition>\d+),\s*"
        r"other dues\s+(?:are\s+)?(?P<other_dues>\d+),\s*"
        r"total fee\s*(?:for)?\s*1st semester\s*(?:is\s*)?(?P<first_semester>\d+)\s+and\s+"
        r"total fee\s*(?:for)?\s*2nd\s*&\s*other semesters\s*(?:is\s*)?(?P<other_semesters>\d+)",
        flags=re.IGNORECASE,
    )
    for segment in segments:
        for match in pattern.finditer(segment):
            program = clean_program_name(match.group("program"))
            program = re.sub(
                r"^.*?\b((?:BS|BSc|M\.Phil/MS|MPhil/MS|MS|Ph\.D|PhD|Diploma|LLB|BBA|MBA|Pharm-D|DVM|Doctor|Generic|BDS|MBBS)\b)",
                r"\1", program, flags=re.I
            )
            program = clean_program_name(program)
            fees.append({
                "program": program,
                "program_norm": normalize(program),
                "group": match.group("group"),
                "tuition_fee": int(match.group("tuition")),
                "other_dues": int(match.group("other_dues")),
                "total_1st_semester": int(match.group("first_semester")),
                "total_other_semesters": int(match.group("other_semesters")),
                "source": "Revised fee.docx",
                "category": "fees",
            })
    # de-duplicate exact fee rows
    unique, seen = [], set()
    for f in fees:
        key = (f["program_norm"], f["group"], f["tuition_fee"], f["total_1st_semester"])
        if key not in seen:
            seen.add(key); unique.append(f)
    return unique


def detect_program(question: str) -> Optional[str]:
    q = normalize(question)

    # Do not treat broad admission questions as a specific program.
    generic_program_questions = [
        "how to apply", "method to apply", "apply for admission",
        "bachelor admission", "bachelors admission", "bs admission",
        "eligibility criteria for bs", "criteria for bs admission",
        "criteria for bachelors", "bachelor degree admission",
    ]
    if any(phrase in q for phrase in generic_program_questions):
        return None
    for alias, program in sorted(PROGRAM_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(normalize(alias)) + r"\b", q):
            return program
    patterns = [
        r"\b(bs [a-z0-9 &\-/]+)", r"\b(bsc [a-z0-9 &\-/]+)", r"\b(mphil [a-z0-9 &\-/]+)",
        r"\b(ms [a-z0-9 &\-/]+)", r"\b(phd [a-z0-9 &\-/]+)", r"\b(pharm d)", r"\b(pharm-d)",
        r"\b(bba [a-z0-9 &\-/]+)", r"\b(llb [a-z0-9 &\-/]+)", r"\b(dvm)",
    ]
    stop_words = [" group a", " group b", " fee", " fees", " criteria", " admission", " eligibility", " requirement", " requirements", " full", " total", " at iub", " in iub", " of iub"]
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            program = match.group(1)
            for stop in stop_words:
                if stop in program:
                    program = program.split(stop)[0]
            return title_program(program)
    # If query has a program name without BS/Degree, match known fee programs.
    q_words = [w for w in q.split() if len(w) > 2 and w not in {"what", "fee", "fees", "full", "total", "program", "tell", "about", "admission", "criteria", "eligibility", "apply", "method", "bachelor", "bachelors", "iub"}]
    if q_words:
        candidates = []
        for f in build_fee_index():
            p_norm = f["program_norm"]
            hits = sum(1 for w in q_words if w in p_norm)
            if hits:
                candidates.append((hits, len(p_norm), f["program"]))
        if candidates:
            candidates.sort(key=lambda x: (-x[0], x[1]))
            return candidates[0][2]
    return None


def find_fee_records(program: str, group: Optional[str] = None) -> List[Dict]:
    if not program:
        return []
    p_norm = normalize(program)
    all_fees = build_fee_index()
    exact = [f for f in all_fees if f["program_norm"] == p_norm]
    if not exact:
        exact = [
            f for f in all_fees
            if len(f["program_norm"]) >= 6
            and len(p_norm) >= 6
            and (p_norm in f["program_norm"] or f["program_norm"] in p_norm)
        ]
    if group:
        exact = [f for f in exact if f["group"].lower() == group.lower()]
    return sorted(exact, key=lambda f: (0 if f["group"] in ["Group-A", "Group-B"] else 1, f["group"]))


def get_manual_fee_records(program: str, group: Optional[str] = None) -> List[Dict]:
    """Small trusted overrides for fee rows that are often missed by regex parsing."""
    p_norm = normalize(program or "")
    manual = {
        normalize("Doctor of Physical Therapy (DPT) (5 Years Program)"): [
            {"program": "Doctor of Physical Therapy (DPT) (5 Years Program)", "program_norm": normalize("Doctor of Physical Therapy (DPT) (5 Years Program)"), "group": "Group-A", "tuition_fee": 41760, "other_dues": 27130, "total_1st_semester": 68890, "total_other_semesters": 55380, "source": "Revised fee.docx", "category": "fees"},
            {"program": "Doctor of Physical Therapy (DPT) (5 Years Program)", "program_norm": normalize("Doctor of Physical Therapy (DPT) (5 Years Program)"), "group": "Group-B", "tuition_fee": 66985, "other_dues": 27130, "total_1st_semester": 94115, "total_other_semesters": 80605, "source": "Revised fee.docx", "category": "fees"},
        ],
        normalize("BS Chemistry"): [
            {"program": "BS Chemistry", "program_norm": normalize("BS Chemistry"), "group": "Group-A", "tuition_fee": 37540, "other_dues": 27130, "total_1st_semester": 64670, "total_other_semesters": 51160, "source": "Revised fee.docx", "category": "fees"},
            {"program": "BS Chemistry", "program_norm": normalize("BS Chemistry"), "group": "Group-B", "tuition_fee": 46975, "other_dues": 27130, "total_1st_semester": 74105, "total_other_semesters": 60595, "source": "Revised fee.docx", "category": "fees"},
        ],
        normalize("BSc Electrical Engineering"): [
            {"program": "BSc Electrical Engineering", "program_norm": normalize("BSc Electrical Engineering"), "group": "Group-A", "tuition_fee": 41760, "other_dues": 27130, "total_1st_semester": 68890, "total_other_semesters": 55380, "source": "Revised fee.docx", "category": "fees"},
            {"program": "BSc Electrical Engineering", "program_norm": normalize("BSc Electrical Engineering"), "group": "Group-B", "tuition_fee": 66985, "other_dues": 27130, "total_1st_semester": 94115, "total_other_semesters": 80605, "source": "Revised fee.docx", "category": "fees"},
        ],
    }
    records = manual.get(p_norm, [])
    if group:
        records = [r for r in records if r["group"].lower() == group.lower()]
    return records


def find_fee_records_safe(program: str, group: Optional[str] = None) -> List[Dict]:
    records = find_fee_records(program, group)
    if records:
        return records
    return get_manual_fee_records(program, group)


@lru_cache(maxsize=1)
def build_people_index() -> List[Dict]:
    people = []
    for doc in load_cleaned_documents():
        text, source, category = doc.get("text", ""), doc.get("source", ""), doc.get("category", "")
        patterns = [
            r"([A-Z][A-Za-z .'-]+?)\s+serves as\s+([^\.\n]+)",
            r"([A-Z][A-Za-z .'-]+?)\s+works as\s+([^\.\n]+)",
            r"([A-Z][A-Za-z .'-]+?)\s*:\s*([^\n\.]*?(?:Chairman|Chairperson|Dean|Director|Incharge|Officer|Registrar|Treasurer)[^\n\.]*)",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                name, designation = match.group(1).strip(), match.group(2).strip()
                if 2 <= len(name.split()) <= 7 and len(designation) <= 180:
                    people.append({"name": name, "designation": designation, "name_norm": normalize(name), "designation_norm": normalize(designation), "source": source, "category": category})
    people.append({"name": "Prof. Dr. Engr. Muhammad Kamran", "designation": "Vice Chancellor", "name_norm": normalize("Prof. Dr. Engr. Muhammad Kamran"), "designation_norm": normalize("Vice Chancellor"), "source": "Vice chancellor.docx", "category": "faculty and departments"})
    unique, seen = [], set()
    for p in people:
        key = (p["name_norm"], p["designation_norm"], p["source"])
        if key not in seen:
            seen.add(key); unique.append(p)
    return unique


def find_person_by_designation(designation_query: str) -> List[Dict]:
    q = normalize(designation_query)
    people = build_people_index()
    if "director it" in q or "head of it" in q:
        priority = [p for p in people if "director it" in p["designation_norm"]]
        if priority: return priority
    if "vc" in q or "vice chancellor" in q:
        priority = [p for p in people if "vice chancellor" in p["designation_norm"]]
        if priority: return priority
    words = [w for w in q.split() if len(w) > 2]
    scored = []
    for p in people:
        score = sum(1 for w in words if w in p["designation_norm"])
        if score:
            scored.append((score, p))
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:3]]


def find_person_by_name(question: str) -> List[Dict]:
    q = normalize(question)
    return [p for p in build_people_index() if p["name_norm"] in q]


def get_campus_list() -> List[Dict]:
    return [{"name": doc.get("source", "").rsplit(".", 1)[0], "source": doc.get("source", ""), "category": "campuses"} for doc in get_docs_by_category("campuses")]


def get_scholarship_list() -> List[Dict]:
    return [{"name": doc.get("source", "").rsplit(".", 1)[0], "source": doc.get("source", ""), "category": "scholarships"} for doc in get_docs_by_category("scholarships")]


def find_admission_context(program: str) -> Optional[Dict]:
    if not program: return None
    text = get_doc_text("Admissions_Criteria_Paragraphsupdated.docx")
    p_norm = normalize(program)
    aliases = [p_norm]
    if p_norm == "bs computer science": aliases.extend(["bs cs", "bs cs", "department of computer science", "computer science"])
    elif p_norm == "doctor of physical therapy dpt 5 years program": aliases.extend(["doctor of physical therapy", "department of physical therapy"])
    parts = re.split(r"\n+|(?<=\.)\s+", text)
    for part in parts:
        if any(alias in normalize(part) for alias in aliases):
            return {"program": program, "text": part.strip(), "source": "Admissions_Criteria_Paragraphsupdated.docx", "category": "admission"}
    return None


def get_hostel_facilities_text() -> Optional[Dict]:
    text = get_doc_text("residential and hostel facilities.docx")
    return {"text": text, "source": "residential and hostel facilities.docx", "category": "hostels"} if text else None


def get_contact_text() -> Optional[Dict]:
    text = get_doc_text("contact .docx")
    return {"text": text, "source": "contact .docx", "category": "contact"} if text else None


def detect_faculty(question: str) -> Optional[str]:
    q = normalize(question)
    for faculty, info in FACULTY_DATA.items():
        for alias in info["aliases"] + [faculty]:
            if normalize(alias) in q:
                return faculty
    # loose matching by key content words
    for faculty in FACULTY_DATA:
        words = [w for w in normalize(faculty).split() if w not in {"faculty", "of", "and"}]
        if words and all(w in q for w in words[:2]):
            return faculty
    return None


def find_faculty_dean(faculty: str) -> Optional[Dict]:
    """
    Return dean only when the designation clearly belongs to the exact faculty.
    Loose word matching caused wrong answers such as treating Online and Distance
    Education as Faculty of Education, so this function is intentionally strict.
    """
    faculty_norm = normalize(faculty)
    faculty_key = faculty_norm.replace("faculty of ", "").replace("faculty ", "")

    for p in build_people_index():
        d = p["designation_norm"]
        if "dean" not in d:
            continue
        if faculty_norm in d or faculty_key in d:
            return p

    return None


def detect_department(question: str) -> Optional[Dict]:
    q = normalize(question)
    for faculty, info in FACULTY_DATA.items():
        for unit, programs in info["units"].items():
            u_norm = normalize(unit)
            if u_norm in q or ("department of " + u_norm) in q:
                return {"faculty": faculty, "unit": unit, "programs": programs}
    return None


def detect_hostel_campus(question: str) -> Optional[Dict]:
    q = normalize(question)
    if "hostel" not in q and "hostels" not in q:
        return None
    for key, data in HOSTEL_CAMPUS_DATA.items():
        if key in q:
            return data
    return None
