import os
import re
import json
from collections import defaultdict


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")

CLEANED_DOCS_PATH = os.path.join(PROCESSED_DIR, "cleaned_documents.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "evaluation_questions_strict.json")


STATIC_CORE_QUESTIONS = [
    {
        "id": "about_university_overview",
        "question": "What is The Islamia University of Bahawalpur?",
        "expected_keywords": ["Islamia University of Bahawalpur"],
        "expected_category": "about university",
        "expected_source": "",
        "question_type": "university_overview",
        "difficulty": "easy"
    },
    {
        "id": "about_university_history",
        "question": "Tell me the history of IUB.",
        "expected_keywords": ["Jamia Abbasia", "1975"],
        "expected_category": "about university",
        "expected_source": "",
        "question_type": "history",
        "difficulty": "easy"
    },
    {
        "id": "about_university_governance",
        "question": "What is the governance structure of IUB?",
        "expected_keywords": ["governance"],
        "expected_category": "about university",
        "expected_source": "",
        "question_type": "governance",
        "difficulty": "medium"
    },
    {
        "id": "about_university_ranking",
        "question": "What is the ranking of IUB?",
        "expected_keywords": ["ranking"],
        "expected_category": "about university",
        "expected_source": "",
        "question_type": "ranking",
        "difficulty": "medium"
    },
    {
        "id": "campuses_list",
        "question": "What campuses does IUB have?",
        "expected_keywords": ["Campus"],
        "expected_category": "campuses",
        "expected_source": "",
        "question_type": "campus_list",
        "difficulty": "easy"
    },
    {
        "id": "campuses_main_location",
        "question": "Where is the main campus of IUB located?",
        "expected_keywords": ["Baghdad-ul-Jadeed", "Hasilpur Road"],
        "expected_category": "campuses",
        "expected_source": "",
        "question_type": "campus_location",
        "difficulty": "easy"
    },
    {
        "id": "admission_bs_criteria",
        "question": "What is the admission criteria for BS programs?",
        "expected_keywords": ["FA", "FSc", "Bachelor"],
        "expected_category": "admission",
        "expected_source": "",
        "question_type": "admission_criteria",
        "difficulty": "easy"
    },
    {
        "id": "admission_apply",
        "question": "How can I apply for admission at IUB?",
        "expected_keywords": ["apply", "admission"],
        "expected_category": "admission",
        "expected_source": "",
        "question_type": "how_to_apply",
        "difficulty": "medium"
    },
    {
        "id": "admission_merit",
        "question": "What is the merit determination policy at IUB?",
        "expected_keywords": ["merit"],
        "expected_category": "admission",
        "expected_source": "",
        "question_type": "merit_policy",
        "difficulty": "medium"
    },
    {
        "id": "fees_bs_structure",
        "question": "What is the fee structure for BS programs at IUB?",
        "expected_keywords": ["fee"],
        "expected_category": "fees",
        "expected_source": "",
        "question_type": "fee_structure",
        "difficulty": "medium"
    },
    {
        "id": "fees_hostel_dues",
        "question": "Are hostel dues included in the fee structure?",
        "expected_keywords": ["Hostel dues", "not included"],
        "expected_category": "fees",
        "expected_source": "",
        "question_type": "fee_policy",
        "difficulty": "hard"
    },
    {
        "id": "fees_transport_charges",
        "question": "Are transport charges included in the fee structure?",
        "expected_keywords": ["transport charges", "not included"],
        "expected_category": "fees",
        "expected_source": "",
        "question_type": "fee_policy",
        "difficulty": "hard"
    },
    {
        "id": "hostels_facilities",
        "question": "What hostel facilities are available at IUB?",
        "expected_keywords": ["hostel", "cafeteria", "dining hall"],
        "expected_category": "hostels",
        "expected_source": "",
        "question_type": "hostel_facilities",
        "difficulty": "easy"
    },
    {
        "id": "hostels_count",
        "question": "How many hostels are available at IUB?",
        "expected_keywords": ["hostels"],
        "expected_category": "hostels",
        "expected_source": "",
        "question_type": "hostel_count",
        "difficulty": "medium"
    },
    {
        "id": "scholarships_list",
        "question": "What scholarships are available at IUB?",
        "expected_keywords": ["Scholarship"],
        "expected_category": "scholarships",
        "expected_source": "",
        "question_type": "scholarship_list",
        "difficulty": "easy"
    },
    {
        "id": "contact_general",
        "question": "What is the contact information of IUB?",
        "expected_keywords": ["phone", "email"],
        "expected_category": "contact",
        "expected_source": "",
        "question_type": "contact",
        "difficulty": "easy"
    },
    {
        "id": "contact_admission",
        "question": "How can I contact the IUB admission office?",
        "expected_keywords": ["admission", "phone", "email"],
        "expected_category": "contact",
        "expected_source": "",
        "question_type": "admission_contact",
        "difficulty": "medium"
    },
    {
        "id": "facilities_student",
        "question": "What facilities are available for students at IUB?",
        "expected_keywords": ["students"],
        "expected_category": "facilities",
        "expected_source": "",
        "question_type": "student_facilities",
        "difficulty": "medium"
    },
    {
        "id": "doit_director",
        "question": "Who is the Director of IT at IUB?",
        "expected_keywords": ["Director IT"],
        "expected_category": "faculty and departments",
        "expected_source": "",
        "question_type": "director_it",
        "difficulty": "easy"
    },
    {
        "id": "doit_overview",
        "question": "Explain about DOIT.",
        "expected_keywords": ["Directorate of Information Technology"],
        "expected_category": "faculty and departments",
        "expected_source": "",
        "question_type": "directorate_overview",
        "difficulty": "medium"
    }
]


BAD_ENTITY_WORDS = [
    "continues with",
    "where",
    "includes",
    "has tuition fee",
    "tuition fee",
    "other dues",
    "total fee",
    "1st semester",
    "2nd",
    "group-a",
    "group-b",
    "eligibility",
    "criteria",
    "requires",
    "requiring",
    "offers bs",
    "offers b",
    "offers m",
    "offers ph",
    "admission",
    "merit",
    "percentage",
    "matric",
    "fa/fsc",
    "fsc",
    "1st division",
    "pre medical",
    "pre engineering",
    "email",
    "phone",
    "contact information",
    "qualification",
    "research interests",
    "publications",
    "profile",
    "address",
    "obtained marks",
    "same criteria",
    "same eligibility",
]

BAD_ENTITY_ENDINGS = [
    "and",
    "of",
    "with",
    "where",
    "includes",
    "continues",
    "continues with",
    "has",
    "offers",
    "after",
    "both",
    "all",
    "same",
]


PROGRAM_PREFIXES = [
    "BS",
    "B.S.",
    "MS",
    "M.S.",
    "M.Phil",
    "MPhil",
    "Ph.D",
    "PhD",
    "BBA",
    "MBA",
    "LLB",
    "B.Ed",
    "M.Ed",
    "Diploma",
]


INVALID_PROGRAM_WORDS = [
    "equivalent",
    "for candidates",
    "candidate",
    "after",
    "in three modes",
    "the 4-year program",
    "the 2.5-year program",
    "the 1.5-year program",
    "obtained marks",
    "eligibility",
    "criteria",
    "merit",
    "requires",
    "requiring",
    "same",
    "group",
    "tuition",
    "fee",
    "dues",
    "semester",
    "department of",
    "faculty of",
    "where",
    "includes",
    "both",
    "all",
    "spanning",
    "science?",
]


PROGRAM_ALIASES = {
    "bs (cs": "BS Computer Science",
    "bs (cs)": "BS Computer Science",
    "bs cs": "BS Computer Science",
    "bs computer science": "BS Computer Science",

    "bs (is": "BS Information Security",
    "bs (is)": "BS Information Security",
    "bs is": "BS Information Security",

    "bs (it": "BS Information Technology",
    "bs (it)": "BS Information Technology",
    "bs it": "BS Information Technology",

    "bs artificial intelligence": "BS Artificial Intelligence",
    "bs data science": "BS Data Science",
    "bs software engineering": "BS Software Engineering",
}


def normalize_spaces(text):
    return re.sub(r"\s+", " ", text).strip()


def slugify(text, max_len=90):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text[:max_len] if text else "item"


def load_cleaned_documents():
    if not os.path.exists(CLEANED_DOCS_PATH):
        raise FileNotFoundError(
            f"cleaned_documents.json not found at {CLEANED_DOCS_PATH}. "
            "Run this first: python -m rag.ingest"
        )

    with open(CLEANED_DOCS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def add_question(question_map, item):
    key = item["question"].lower().strip()

    if key in question_map:
        return

    question_map[key] = item


def clean_entity(entity):
    entity = normalize_spaces(entity)
    entity = entity.strip(" .,:;|-()")

    cut_patterns = [
        r"\bcontinues with\b",
        r"\bwhere\b",
        r"\bincludes\b",
        r"\bhas tuition fee\b",
        r"\bwith tuition fee\b",
        r"\boffers\b",
        r"\brequires\b",
        r"\brequiring\b",
        r"\bunder\b",
        r"\balong with\b",
        r"\bhas\b",
    ]

    for pattern in cut_patterns:
        match = re.search(pattern, entity, flags=re.IGNORECASE)
        if match:
            entity = entity[:match.start()].strip(" .,:;|-()")

    for ending in BAD_ENTITY_ENDINGS:
        if entity.lower().endswith(" " + ending):
            entity = entity[: -len(ending)].strip(" .,:;|-()")

    return entity


def is_valid_entity(entity):
    if not entity:
        return False

    entity = normalize_spaces(entity)
    lower = entity.lower()

    if len(entity) < 8 or len(entity) > 90:
        return False

    alpha_count = sum(ch.isalpha() for ch in entity)

    if alpha_count < 6:
        return False

    if entity.count(" ") > 10:
        return False

    for bad in BAD_ENTITY_WORDS:
        if bad in lower:
            return False

    for ending in BAD_ENTITY_ENDINGS:
        if lower.endswith(" " + ending):
            return False

    if re.search(r"\b(1st|2nd|3rd|4th|5th)\b", lower):
        return False

    if "/" in entity and not entity.lower().startswith("department"):
        return False

    return True


def get_sentences(text):
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [normalize_spaces(p) for p in parts if normalize_spaces(p)]


def clean_program_name(program):
    program = normalize_spaces(program)
    program = program.strip(" .,:;|-()?/")

    program = program.replace("B. S.", "BS")
    program = program.replace("B.S.", "BS")
    program = program.replace("M. Phil", "MPhil")
    program = program.replace("M.Phil", "MPhil")
    program = program.replace("Ph. D", "PhD")
    program = program.replace("Ph.D", "PhD")

    lower_program = program.lower().strip()

    for alias, normalized in PROGRAM_ALIASES.items():
        if lower_program == alias:
            return normalized

    cut_patterns = [
        r"\bgroup[- ]?[ab]\b",
        r"\bhas\b",
        r"\bwith\b",
        r"\bwhere\b",
        r"\btuition\b",
        r"\bother\b",
        r"\btotal\b",
        r"\brequires\b",
        r"\brequiring\b",
        r"\bcriteria\b",
        r"\bmerit\b",
        r"\bpercentage\b",
        r"\bafter\b",
        r"\bfor candidates\b",
        r"\bunder\b",
        r"\balong with\b",
        r"\bspanning\b",
    ]

    for pattern in cut_patterns:
        match = re.search(pattern, program, flags=re.IGNORECASE)
        if match:
            program = program[:match.start()].strip(" .,:;|-()?/")

    program = program.strip(" .,:;|-()?/")

    for ending in BAD_ENTITY_ENDINGS:
        if program.lower().endswith(" " + ending):
            program = program[: -len(ending)].strip(" .,:;|-()?/")

    return normalize_spaces(program)


def is_valid_program(program):
    if not program:
        return False

    program = normalize_spaces(program)
    lower = program.lower()

    if len(program) < 5 or len(program) > 70:
        return False

    if program.count(" ") > 7:
        return False

    if program.endswith("(") or program.endswith("&") or program.endswith("/") or program.endswith("?"):
        return False

    if "(" in program and ")" not in program:
        return False

    if "/" in program:
        return False

    for bad in INVALID_PROGRAM_WORDS:
        if bad in lower:
            return False

    if lower in ["b.ed", "m.ed", "bs", "ms", "phd", "mphil", "diploma"]:
        return False

    if lower.startswith("adp"):
        return False

    valid_start = False

    for prefix in PROGRAM_PREFIXES:
        if lower.startswith(prefix.lower()):
            valid_start = True
            break

    if not valid_start:
        return False

    return True


def extract_programs_from_sentence(sentence):
    programs = set()

    prefix_pattern = r"(?:BS|B\.S\.|MS|M\.S\.|M\.Phil|MPhil|Ph\.D|PhD|BBA|MBA|LLB|B\.Ed|M\.Ed|Diploma)"

    matches = list(re.finditer(prefix_pattern, sentence))

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(sentence)

        raw = sentence[start:end]

        raw = re.split(
            r"\b(?:requires|requiring|has|with|where|under|along with|merit|eligibility|criteria|fee|tuition|spanning|for candidates)\b",
            raw,
            flags=re.IGNORECASE
        )[0]

        raw = raw.strip(" .,:;|-?/")

        cleaned = clean_program_name(raw)

        if is_valid_program(cleaned):
            programs.add(cleaned)

    return programs


def extract_program_names(text):
    programs = set()

    for sentence in get_sentences(text):
        sentence_programs = extract_programs_from_sentence(sentence)

        for program in sentence_programs:
            programs.add(program)

    return sorted(programs)


def extract_faculty_entities(text):
    entities = set()

    patterns = [
        r"\bFaculty of [A-Z][A-Za-z &,\-()]+",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text):
            entity = clean_entity(match)

            if is_valid_entity(entity):
                entities.add(entity)

    return sorted(entities)


def extract_department_entities(text):
    entities = set()

    patterns = [
        r"\bDepartment of [A-Z][A-Za-z &,\-()]+",
        r"\bDeptt\. Of [A-Z][A-Za-z &,\-()]+",
        r"\bDeptt\. of [A-Z][A-Za-z &,\-()]+",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text):
            entity = clean_entity(match)
            entity = re.sub(r"Deptt\. Of", "Department of", entity)
            entity = re.sub(r"Deptt\. of", "Department of", entity)

            if is_valid_entity(entity):
                entities.add(entity)

    return sorted(entities)


def extract_directorate_entities(text):
    entities = set()

    patterns = [
        r"\bDirectorate of [A-Z][A-Za-z &,\-()]+",
        r"\bDirectorate [A-Z][A-Za-z &,\-()]+",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text):
            entity = clean_entity(match)

            entity = re.split(
                r",\s*(Engr|Dr|Prof|Mr|Ms|Mrs)\b",
                entity,
                flags=re.IGNORECASE
            )[0].strip(" .,:;|-()")

            if is_valid_entity(entity):
                entities.add(entity)

    return sorted(entities)


def extract_division_entities(text):
    entities = set()

    patterns = [
        r"\b[A-Z][A-Za-z &,\-()]+ Division\b",
        r"\bDivision of [A-Z][A-Za-z &,\-()]+",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text):
            entity = clean_entity(match)

            if is_valid_entity(entity):
                entities.add(entity)

    return sorted(entities)


def extract_center_entities(text):
    entities = set()

    patterns = [
        r"\b[A-Z][A-Za-z &,\-()]+ Center\b",
        r"\b[A-Z][A-Za-z &,\-()]+ Centre\b",
        r"\bCenter for [A-Z][A-Za-z &,\-()]+",
        r"\bCentre for [A-Z][A-Za-z &,\-()]+",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text):
            entity = clean_entity(match)

            if is_valid_entity(entity):
                entities.add(entity)

    return sorted(entities)


def extract_institute_entities(text):
    entities = set()

    patterns = [
        r"\bInstitute of [A-Z][A-Za-z &,\-()]+",
        r"\bInstitute [A-Z][A-Za-z &,\-()]+",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text):
            entity = clean_entity(match)

            if is_valid_entity(entity):
                entities.add(entity)

    return sorted(entities)


def extract_office_entities(text):
    entities = set()

    patterns = [
        r"\bOffice of [A-Z][A-Za-z &,\-()]+",
        r"\b[A-Z][A-Za-z &,\-()]+ Office\b",
    ]

    invalid_offices = [
        "The Office",
        "In the Office",
        "This Office",
        "That Office",
        "Office of the",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text):
            entity = clean_entity(match)

            if entity in invalid_offices:
                continue

            if entity.lower().startswith("in the "):
                continue

            if entity.lower().startswith("the "):
                continue

            if entity.lower() == "office of the":
                continue

            if is_valid_entity(entity):
                entities.add(entity)

    return sorted(entities)


def detect_scholarship_name(source, text):
    source_name = os.path.splitext(source)[0].strip()

    if "scholarship" in source_name.lower():
        return source_name

    first_text = " ".join(text.splitlines()[:8])

    match = re.search(
        r"\b[A-Z][A-Za-z &,\-]+ Scholarship(?: Program)?\b",
        first_text
    )

    if match:
        name = clean_entity(match.group(0))

        if is_valid_entity(name):
            return name

    return None


def has_scholarship_eligibility_info(text):
    lower = text.lower()

    eligibility_words = [
        "eligibility",
        "eligible",
        "criteria",
        "who can apply",
        "students must",
        "applicant must",
        "required",
        "requirements",
    ]

    for word in eligibility_words:
        if word in lower:
            return True

    return False


def detect_campus_name(source, text):
    source_name = os.path.splitext(source)[0].strip()

    if "campus" in source_name.lower():
        return source_name

    match = re.search(r"\b[A-Z][A-Za-z\- ]+ Campus\b", text[:1500])

    if match:
        name = clean_entity(match.group(0))

        if is_valid_entity(name):
            return name

    return None


def detect_facility_topic(source):
    name = os.path.splitext(source)[0].strip()

    if not name:
        return None

    bad_names = ["desktop", "document", "file"]

    if name.lower() in bad_names:
        return None

    return name


def make_faculty_questions(entity, source):
    base = slugify(entity)

    return [
        {
            "id": f"faculty_{base}_overview",
            "question": f"Tell me about {entity}.",
            "expected_keywords": [entity],
            "expected_category": "faculty and departments",
            "expected_source": source,
            "question_type": "faculty_overview",
            "difficulty": "hard"
        },
        {
            "id": f"faculty_{base}_departments",
            "question": f"What departments are under {entity}?",
            "expected_keywords": [entity, "Department"],
            "expected_category": "faculty and departments",
            "expected_source": source,
            "question_type": "faculty_departments",
            "difficulty": "hard"
        }
    ]


def make_department_questions(entity, source):
    base = slugify(entity)

    return [
        {
            "id": f"department_{base}_overview",
            "question": f"Tell me about {entity}.",
            "expected_keywords": [entity],
            "expected_category": "faculty and departments",
            "expected_source": source,
            "question_type": "department_overview",
            "difficulty": "hard"
        },
        {
            "id": f"department_{base}_programs",
            "question": f"What programs are offered in {entity}?",
            "expected_keywords": [entity],
            "expected_category": "faculty and departments",
            "expected_source": source,
            "question_type": "department_programs",
            "difficulty": "hard"
        }
    ]


def make_directorate_questions(entity, source):
    base = slugify(entity)

    return [
        {
            "id": f"directorate_{base}_overview",
            "question": f"What is {entity}?",
            "expected_keywords": [entity],
            "expected_category": "faculty and departments",
            "expected_source": source,
            "question_type": "directorate_overview",
            "difficulty": "medium"
        },
        {
            "id": f"directorate_{base}_contact",
            "question": f"What is the contact information of {entity}?",
            "expected_keywords": [entity],
            "expected_category": "faculty and departments",
            "expected_source": source,
            "question_type": "directorate_contact",
            "difficulty": "medium"
        }
    ]


def make_simple_entity_questions(entity, source, entity_type):
    base = slugify(entity)

    return [
        {
            "id": f"{entity_type}_{base}_overview",
            "question": f"Tell me about {entity}.",
            "expected_keywords": [entity],
            "expected_category": "faculty and departments",
            "expected_source": source,
            "question_type": f"{entity_type}_overview",
            "difficulty": "hard"
        }
    ]


def make_program_admission_question(program, source):
    base = slugify(program)

    return {
        "id": f"program_{base}_admission",
        "question": f"What is the admission criteria for {program}?",
        "expected_keywords": [program],
        "expected_category": "admission",
        "expected_source": source,
        "question_type": "program_admission",
        "difficulty": "medium"
    }


def make_program_fee_question(program, source):
    base = slugify(program)

    return {
        "id": f"program_{base}_fee",
        "question": f"What is the fee structure for {program}?",
        "expected_keywords": [program, "fee"],
        "expected_category": "fees",
        "expected_source": source,
        "question_type": "program_fee",
        "difficulty": "medium"
    }


def make_campus_questions(name, source):
    base = slugify(name)

    return [
        {
            "id": f"campus_{base}_overview",
            "question": f"Tell me about {name}.",
            "expected_keywords": [name],
            "expected_category": "campuses",
            "expected_source": source,
            "question_type": "campus_overview",
            "difficulty": "medium"
        },
        {
            "id": f"campus_{base}_facilities",
            "question": f"What facilities are available at {name}?",
            "expected_keywords": [name],
            "expected_category": "campuses",
            "expected_source": source,
            "question_type": "campus_facilities",
            "difficulty": "medium"
        }
    ]


def make_facility_questions(topic, source):
    base = slugify(topic)

    return [
        {
            "id": f"facility_{base}_overview",
            "question": f"Tell me about {topic} facility at IUB.",
            "expected_keywords": [topic.split()[0]],
            "expected_category": "facilities",
            "expected_source": source,
            "question_type": "facility_overview",
            "difficulty": "medium"
        }
    ]


def generate_questions():
    documents = load_cleaned_documents()

    question_map = {}

    for item in STATIC_CORE_QUESTIONS:
        add_question(question_map, item)

    seen_entities = set()
    seen_program_admissions = set()
    seen_program_fees = set()
    seen_scholarships = set()
    seen_campuses = set()
    seen_facilities = set()

    category_counts = defaultdict(int)
    type_counts = defaultdict(int)

    for doc in documents:
        text = doc.get("text", "")
        category = doc.get("category", "")
        source = doc.get("source", "")

        category_counts[category] += 1

        if category == "faculty and departments":
            entity_groups = [
                ("faculty", extract_faculty_entities),
                ("department", extract_department_entities),
                ("directorate", extract_directorate_entities),
                ("division", extract_division_entities),
                ("center", extract_center_entities),
                ("institute", extract_institute_entities),
                ("office", extract_office_entities),
            ]

            for entity_type, extractor in entity_groups:
                entities = extractor(text)

                for entity in entities:
                    key = (entity_type, entity.lower(), source)

                    if key in seen_entities:
                        continue

                    seen_entities.add(key)

                    if entity_type == "faculty":
                        generated = make_faculty_questions(entity, source)
                    elif entity_type == "department":
                        generated = make_department_questions(entity, source)
                    elif entity_type == "directorate":
                        generated = make_directorate_questions(entity, source)
                    else:
                        generated = make_simple_entity_questions(
                            entity=entity,
                            source=source,
                            entity_type=entity_type
                        )

                    for q in generated:
                        add_question(question_map, q)

        elif category == "admission":
            programs = extract_program_names(text)

            for program in programs:
                key = program.lower()

                if key in seen_program_admissions:
                    continue

                seen_program_admissions.add(key)

                q = make_program_admission_question(program, source)
                add_question(question_map, q)

        elif category == "fees":
            programs = extract_program_names(text)

            for program in programs:
                key = program.lower()

                if key in seen_program_fees:
                    continue

                seen_program_fees.add(key)

                q = make_program_fee_question(program, source)
                add_question(question_map, q)

        elif category == "scholarships":
            scholarship_name = detect_scholarship_name(source, text)

            if scholarship_name:
                key = scholarship_name.lower()

                if key not in seen_scholarships:
                    seen_scholarships.add(key)

                    base = slugify(scholarship_name)

                    overview_question = {
                        "id": f"scholarship_{base}_overview",
                        "question": f"What is the {scholarship_name}?",
                        "expected_keywords": [scholarship_name.split()[0], "Scholarship"],
                        "expected_category": "scholarships",
                        "expected_source": source,
                        "question_type": "scholarship_overview",
                        "difficulty": "medium"
                    }

                    add_question(question_map, overview_question)

                    if has_scholarship_eligibility_info(text):
                        eligibility_question = {
                            "id": f"scholarship_{base}_eligibility",
                            "question": f"What is the eligibility criteria for {scholarship_name}?",
                            "expected_keywords": ["eligibility"],
                            "expected_category": "scholarships",
                            "expected_source": source,
                            "question_type": "scholarship_eligibility",
                            "difficulty": "medium"
                        }

                        add_question(question_map, eligibility_question)

        elif category == "campuses":
            campus_name = detect_campus_name(source, text)

            if campus_name:
                key = campus_name.lower()

                if key not in seen_campuses:
                    seen_campuses.add(key)

                    generated = make_campus_questions(campus_name, source)

                    for q in generated:
                        add_question(question_map, q)

        elif category == "facilities":
            topic = detect_facility_topic(source)

            if topic:
                key = topic.lower()

                if key not in seen_facilities:
                    seen_facilities.add(key)

                    generated = make_facility_questions(topic, source)

                    for q in generated:
                        add_question(question_map, q)

    final_questions = list(question_map.values())

    for q in final_questions:
        type_counts[q.get("question_type", "unknown")] += 1

    return final_questions, category_counts, type_counts


def save_questions(questions):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(questions, file, indent=2, ensure_ascii=False)


def main():
    print("Generating final cleaned evaluation questions from real IUB data...")
    print(f"Reading: {CLEANED_DOCS_PATH}")

    try:
        questions, category_counts, type_counts = generate_questions()
    except FileNotFoundError as error:
        print(error)
        return

    save_questions(questions)

    print("\nEvaluation file generated successfully.")
    print(f"Output file: {OUTPUT_PATH}")
    print(f"Total questions generated: {len(questions)}")

    print("\nDocuments by category:")
    for category, count in sorted(category_counts.items()):
        print(f"- {category}: {count}")

    print("\nQuestions by type:")
    for question_type, count in sorted(type_counts.items()):
        print(f"- {question_type}: {count}")


if __name__ == "__main__":
    main()