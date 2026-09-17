import json
import os
import re
from typing import Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(BASE_DIR, "knowledge_base")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")
CLEANED_DOCS_PATH = os.path.join(PROCESSED_DIR, "cleaned_documents.json")

FALLBACK_ANSWER = "Sorry, I could not find official information about this."

STOP_WORDS = {
    "what", "is", "are", "the", "of", "in", "at", "iub", "fee", "fees", "full", "total", "tell", "about",
    "program", "programs", "department", "departments", "faculty", "faculties", "admission", "criteria",
    "eligibility", "requirement", "requirements", "apply", "method", "procedure", "for", "to", "me", "please", "and", "with",
    "bachelor", "bachelors", "bs", "bsc", "group", "a", "b", "can", "get", "i", "belong", "province",
    "semester", "structure"
}


def load_json(name: str, default):
    path = os.path.join(KB_DIR, name)
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_cleaned_document(source_name: str) -> Optional[Dict]:
    if not os.path.exists(CLEANED_DOCS_PATH):
        return None
    with open(CLEANED_DOCS_PATH, "r", encoding="utf-8") as file:
        documents = json.load(file)
    wanted = normalize(source_name)
    for doc in documents:
        if normalize(doc.get("source", "")) == wanted:
            return doc
    return None


def normalize(text: str) -> str:
    text = str(text or "").lower()
    replacements = {
        "&": " and ",
        "v.c": "vc",
        "v c": "vc",
        "vice chancellor": "vice chancellor",
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
        "physical therapist": "physical therapy",
        "doctor of phisio therapist": "doctor of physical therapy",
        "baghdad ul jadeed": "baghdad-ul-jadeed",
        "baghdad-ul-jaded": "baghdad-ul-jadeed",
        "khwaja": "khawaja",
        "progeams": "programs",
        "ryk": "rahim yar khan",
        "bscs": "bs computer science",
        "bsai": "bs artificial intelligence",
        "bsse": "bs software engineering",
        "bsit": "bs information technology",
        "bsds": "bs data science",
        "kon hai": "who is",
        "kya hai": "what is",
        "kitni hai": "how much",
        "kahan hai": "where is",
        "kahan se": "where",
        "bhool gaya": "forgot",
        "nahi ho raha": "not working",
        "mil jaye ga": "available",
    }
    for old, new in replacements.items():
        if old == "&":
            text = text.replace(old, new)
            continue
        pattern = r"(?<![a-z0-9])" + re.escape(old) + r"(?![a-z0-9])"
        text = re.sub(pattern, new, text)
    text = re.sub(r"[^a-z0-9\s\-/]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokens(text: str) -> List[str]:
    return [w for w in normalize(text).split() if w and w not in STOP_WORDS and len(w) > 1]


def source_item(source: str, category: str, score="kb"):
    return {"source": source, "category": category, "score": score}


def is_greeting(question: str) -> bool:
    q = normalize(question)
    return q in {"hi", "hello", "hey", "salam", "assalam o alaikum", "assalamualaikum"}


def is_fee_query(question: str) -> bool:
    q = normalize(question)
    return any(word in q for word in ["fee", "fees", "dues", "charges", "tuition"])


def is_non_bs_fee_query(question: str) -> bool:
    q = normalize(question)
    if not is_fee_query(q):
        return False
    if any(term in q for term in ["phd", "doctor of philosophy", "mphil", "m phil", "ms ", "master"]):
        return not any(term in q for term in ["pharm-d", "pharm d", "doctor of pharmacy"])
    return False


def is_hostel_fee_query(question: str) -> bool:
    q = normalize(question)
    return is_fee_query(q) and any(word in q for word in ["hostel", "hostels", "living", "accommodation", "boarding"])


def is_admission_procedure_query(question: str) -> bool:
    q = normalize(question)
    return any(phrase in q for phrase in [
        "how to apply", "apply for admission", "method to apply", "procedure to apply", "admission procedure",
        "full method", "application procedure", "admission process"
    ])


def is_result_awaiting_query(question: str) -> bool:
    q = normalize(question)
    return any(phrase in q for phrase in [
        "result awaiting",
        "awaiting result",
        "result is awaiting",
        "result awaited",
        "waiting for result",
        "result not announced",
    ])


def is_5th_semester_query(question: str) -> bool:
    q = normalize(question)
    return (
        ("5th" in q or "fifth" in q)
        and "semester" in q
        and any(word in q for word in ["admission", "eligible", "eligibility", "criteria", "apply"])
    )


def is_bs_adp_difference_query(question: str) -> bool:
    q = normalize(question)
    return (
        "adp" in q
        and "bs" in q
        and any(word in q for word in ["difference", "different", "compare", "between"])
    )


def is_lms_password_query(question: str) -> bool:
    q = normalize(question)
    return "lms" in q and any(word in q for word in ["password", "reset", "forgot", "recover", "login"])


def is_operational_workflow_query(question: str) -> bool:
    q = normalize(question)
    workflow_words = [
        "portal", "lms", "attendance", "marks", "result", "transcript", "course register",
        "register courses", "freeze", "migration", "personal information", "date sheet",
        "roll number", "paper rechecking", "rechecking", "improvement", "repeat", "degree",
        "duplicate result", "library", "wifi", "wi-fi", "email", "online classes", "internet",
        "faculty portal", "upload attendance", "upload marks", "attendance reports",
        "course material", "assignments", "quizzes", "enrolled students", "award lists",
        "sessional", "marks submission", "wrong marks", "course file", "course outline",
        "exam duty", "invigilation", "unfair means", "answer sheets", "result sheets",
        "duty replacement", "paper setting", "leave balance", "casual leave", "medical leave",
        "joining report", "experience certificate", "noc", "promotion", "faculty profile",
        "research publications", "publications", "research grant", "conference funding",
        "research project", "research policies", "teacher profile", "qualification details",
        "research interests", "upload my cv", "timetable change", "oric", "leave",
        "student absence", "marking deadline", "profile information", "courses assigned",
        "course change", "courses are assigned", "assigned to me", "hec-recognized journals", "hec recognized journals", "my department",
    ]
    if is_lms_password_query(q):
        return True
    return any(word in q for word in workflow_words)


def is_broad_admission_criteria_query(question: str) -> bool:
    q = normalize(question)
    return any(phrase in q for phrase in [
        "eligibility criteria for bs admission", "criteria for bs admission", "eligibility for bs admission",
        "criteria for bachelors", "bachelor admission", "bachelors admission", "bs admission"
    ])


def format_sources(rows: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for row in rows:
        key = (row.get("source"), row.get("category"))
        if key not in seen:
            seen.add(key)
            out.append(source_item(row.get("source"), row.get("category")))
    return out


def format_admission_rows(rows: List[Dict]) -> Dict:
    answer = " ".join(clean_extracted_text(row.get("text", "")) for row in rows if row.get("text"))
    return {
        "answer": answer,
        "sources": format_sources(rows),
    }


def direct_program_criteria_answer(question: str) -> Optional[Dict]:
    q = normalize(question)
    computing_criteria = (
        "ICS/FSc/I.Com or FA with any one of these subjects: Computer Science, Statistics, "
        "Economics, Mathematics, Physics, or Commerce. DAE, A-Level, and IUB Test are also accepted. "
        "Merit is determined on the percentage of obtained marks."
    )
    programs = [
        (["computer science", "bs computer science", "bs cs", "bscs", "cs"], "BS Computer Science"),
        (["artificial intelligence", "bs artificial intelligence", "bs ai", "bsai", "ai"], "BS Artificial Intelligence"),
        (["software engineering", "bs software engineering", "bs se", "bsse", "se"], "BS Software Engineering"),
        (["information technology", "bs information technology", "bs it", "bsit"], "BS Information Technology"),
        (["data science", "data sciences", "bs data science", "bs data sciences", "bsds", "ds"], "BS Data Science"),
    ]
    for aliases, program in programs:
        if any(contains_alias(q, alias) for alias in aliases):
            return {
                "answer": f"{program} admission criteria: {computing_criteria}",
                "sources": [source_item("Admissions_Criteria_Paragraphsupdated.docx", "admission")],
            }
    if contains_alias(q, "chemistry") or contains_alias(q, "bs chemistry"):
        return {
            "answer": "BS Chemistry admission criteria: FSc Pre-Medical or equivalent along with MCAT/IUB Test. Merit is based on percentage of obtained marks.",
            "sources": [source_item("Admissions_Criteria_Paragraphsupdated.docx", "admission")],
        }
    return None


def contains_alias(text: str, alias: str) -> bool:
    text_norm = normalize(text)
    alias_norm = normalize(alias)
    if not alias_norm:
        return False
    if " " in alias_norm or "-" in alias_norm:
        return re.search(r"\b" + re.escape(alias_norm) + r"\b", text_norm) is not None
    return re.search(r"\b" + re.escape(alias_norm) + r"\b", text_norm) is not None


def unavailable_answer(topic: str) -> Dict:
    return {
        "answer": f"Sorry, I could not find official information about {topic}.",
        "sources": [],
    }


def find_program_criteria_rows(question: str, admissions: Dict) -> List[Dict]:
    q = normalize(question)
    aliases = [
        ["data science", "data sciences", "bs data science", "bs data sciences", "bsds", "ds"],
        ["computer science", "bs computer science", "bs cs", "bscs", "cs"],
        ["information technology", "bs information technology", "bs it", "bsit"],
        ["artificial intelligence", "bs artificial intelligence", "bs ai", "bsai", "ai"],
        ["software engineering", "bs software engineering", "bs se", "bsse", "se"],
        ["pharm-d", "pharm d", "doctor of pharmacy"],
        ["doctor of physical therapy", "dpt"],
        ["chemistry", "bs chemistry"],
    ]
    selected_aliases = []
    for group in aliases:
        if any(contains_alias(q, alias) for alias in group):
            selected_aliases = group
            break
    if not selected_aliases:
        return []

    rows = admissions.get("program_criteria", [])
    if any(alias in selected_aliases for alias in ["software engineering", "bs software engineering", "bs se", "bsse", "se"]):
        selected = []
        for row in rows:
            text_norm = normalize(row.get("text", ""))
            if "department of information technology" in text_norm and "data science" in text_norm:
                selected.append(row)
                continue
            if "all these programs share the same admission criteria" in text_norm:
                selected.append(row)
                continue
            if "department of software engineering offers bs software engineering" in text_norm:
                selected.append(row)
                break
        return selected

    if any(alias in selected_aliases for alias in ["chemistry", "bs chemistry"]):
        selected = []
        for row in rows:
            text_norm = normalize(row.get("text", ""))
            if "department of botany offers bs botany" in text_norm:
                selected.append(row)
                continue
            if "department of chemistry offers bs chemistry" in text_norm:
                selected.append(row)
                break
        return selected

    for index, row in enumerate(rows):
        row_text = row.get("text", "")
        if not any(contains_alias(row_text, alias) for alias in selected_aliases):
            continue

        selected = [row]
        for following in rows[index + 1:index + 6]:
            following_norm = normalize(following.get("text", ""))
            if (
                "all these programs" in following_norm
                or following_norm.startswith("merit ")
            ):
                selected.append(following)
        if any("all these programs" in normalize(item.get("text", "")) for item in selected):
            selected = [
                item for item in selected
                if not (
                    normalize(item.get("text", "")).startswith("merit for all these programs")
                    and any("merit is determined" in normalize(other.get("text", "")) for other in selected)
                )
            ]
        return selected
    return []


def clean_extracted_text(text: str) -> str:
    replacements = {
        "seekingadmission": "seeking admission",
        "shewill": "she will",
        "tobecareful": "to be careful",
        "canbe": "can be",
        "thesame": "the same",
        "withall": "with all",
        "inall": "in all",
        "andalso": "and also",
        "Sciecne": "Science",
        "Date Science": "Data Science",
    }
    cleaned = str(text or "").strip()
    for old, new in replacements.items():
        cleaned = re.sub(old, new, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned.count("(") > cleaned.count(")"):
        cleaned += ")"
    return cleaned


def detect_group(question: str, last_question: str = "") -> Optional[str]:
    q = normalize(question + " " + last_question)
    if re.search(r"\bgroup\s*a\b", q):
        return "Group-A"
    if re.search(r"\bgroup\s*b\b", q):
        return "Group-B"
    return None


def program_acronyms(program: str) -> set:
    words = [w for w in re.findall(r"[A-Za-z]+", program) if w.lower() not in {"of", "and", "in", "the", "program", "years", "year"}]
    acronyms = set()
    if words:
        item = "".join(w[0].lower() for w in words)
        if item not in STOP_WORDS:
            acronyms.add(item)
    for match in re.findall(r"\(([A-Za-z\-]{2,10})\)", program):
        acronyms.add(normalize(match))
    # Degree-aware short form: BS Computer Science -> cs, BS Artificial Intelligence -> ai
    degree_words = {"bs", "bsc", "ms", "msc", "mphil", "phd", "doctor", "diploma", "bba", "mba", "llb", "llm"}
    content_words = [w for w in words if w.lower() not in degree_words]
    if content_words:
        item = "".join(w[0].lower() for w in content_words)
        if item not in STOP_WORDS:
            acronyms.add(item)
    return acronyms


def detect_fee_program(question: str, last_question: str = "") -> Optional[str]:
    fees = load_json("fees.json", [])
    if not fees:
        return None
    q_norm = normalize(question)
    # Use previous question only for follow-ups like "what about group B".
    use_last = bool(detect_group(question) and last_question and not is_fee_query(question))
    combined_norm = normalize(question + (" " + last_question if use_last else ""))
    q_tokens = tokens(last_question if use_last else question)
    candidates = {}
    for row in fees:
        program = row.get("program", "")
        p_norm = row.get("program_norm") or normalize(program)
        p_tokens = tokens(program)
        acronyms = set(row.get("acronyms", [])) | program_acronyms(program)
        score = 0
        # Exact phrase / containment
        if p_norm and p_norm in combined_norm:
            score += 100
        # Acronym match like CS, DPT, Pharm-D
        acronym_matched = False
        for acronym in acronyms:
            if acronym and acronym not in STOP_WORDS and re.search(r"\b" + re.escape(acronym) + r"\b", combined_norm):
                acronym_matched = True
                score += 90 if len(acronym) <= 4 else 70

        # Token overlap
        matched_tokens = [t for t in q_tokens if t in p_tokens or t in p_norm]
        hits = len(matched_tokens)
        if hits:
            score += hits * 12

        # Prevent broad/common words from selecting wrong programs.
        # Example: "electronic engineering" should not match "Civil Engineering" only because of "engineering".
        if q_tokens and not acronym_matched:
            missing_specific = [t for t in q_tokens if len(t) >= 4 and t not in p_norm]
            if missing_specific:
                score = 0

        # Avoid choosing generic programs from weak single short-token matches unless an acronym matched.
        distinctive = [t for t in q_tokens if len(t) >= 4]
        if hits == 1 and not distinctive and not acronym_matched:
            score = 0
        if score > 0:
            prev = candidates.get(program)
            if prev is None or score > prev:
                candidates[program] = score
    if not candidates:
        return None
    ranked = sorted(candidates.items(), key=lambda x: (-x[1], len(x[0])))
    # Require a reasonable match so broad queries do not map to random programs
    if ranked[0][1] < 12:
        return None
    return ranked[0][0]


def answer_fee(question: str, last_question: str = "") -> Optional[Dict]:
    # Also handle follow-ups like "what about group B" after a fee question.
    if not is_fee_query(question) and not (detect_group(question) and last_question and is_fee_query(last_question)):
        return None
    q = normalize(question)
    if is_non_bs_fee_query(question):
        return unavailable_answer("fee structure for that degree/program")
    if "transport" in q or "bus" in q:
        return unavailable_answer("transport fee")
    if is_hostel_fee_query(question):
        return {"answer": FALLBACK_ANSWER, "sources": []}
    program = detect_fee_program(question, last_question)
    if not program:
        return {"answer": "Please specify the exact program name so I can answer the fee accurately.", "sources": []}
    group = detect_group(question, last_question)
    fees = [f for f in load_json("fees.json", []) if f.get("program") == program]
    if group:
        fees = [f for f in fees if f.get("group", "").lower() == group.lower()]
    if not fees:
        return {"answer": FALLBACK_ANSWER, "sources": []}
    lines = [f"Fee structure for {program}:"]
    for f in sorted(fees, key=lambda x: x.get("group", "")):
        lines.append(
            f"• {f['group']}: tuition fee {f['tuition_fee']}, other dues {f['other_dues']}, "
            f"1st semester total {f['total_1st_semester']}, 2nd and other semesters total {f['total_other_semesters']}"
        )
    return {"answer": "\n".join(lines), "sources": format_sources(fees)}


def answer_admission_followups(question: str) -> Optional[Dict]:
    q = normalize(question)
    procedure = load_json("admissions.json", {}).get("procedure", {})
    source = source_item(procedure.get("source", "how to apply for admission.docx"), procedure.get("category", "admission"))

    if "document" in q and "admission" in q:
        return unavailable_answer("required admission documents")
    if "last date" in q and "admission" in q:
        return unavailable_answer("the current admission last date")
    if "merit list" in q and any(word in q for word in ["check", "where", "kahan"]):
        return {
            "answer": "Candidates can check the status of their application online. I could not find a separate confirmed merit-list URL.",
            "sources": [source],
        }
    if "name appears" in q or ("merit list" in q and any(word in q for word in ["after", "appears", "appear"])):
        return {
            "answer": "If your name appears in a merit list, appear in person within the due time with all original documents before the respective department admission committee and follow the committee's instructions.",
            "sources": [source],
        }
    if "more than one program" in q or "another program" in q or "multiple program" in q or "two programs" in q:
        return {
            "answer": "If you want to apply to another program or department, go back to the application step. A separate application form and separate challan are required for each program.",
            "sources": [source],
        }
    if "change" in q and "program" in q:
        return {
            "answer": "You can log in with your registration information and password if your information needs to be updated. I could not find a separate confirmed procedure for changing a selected program after submission.",
            "sources": [source],
        }
    if "admission fee" in q or ("submit" in q and "fee" in q) or ("fee" in q and "hbl" in q):
        return {
            "answer": "For the admission processing fee, the system generates a challan after you submit a valid application form. Print the challan and deposit the prescribed fee in the nearest HBL branch.",
            "sources": [source],
        }
    if "entry test" in q:
        return {
            "answer": "Entry-test requirements vary by program. Some programs mention IUB Test, NAT, ECAT, MCAT, HEC test, or LAT. Please ask with the exact program name for the precise requirement.",
            "sources": [source_item("Admissions_Criteria_Paragraphsupdated.docx", "admission")],
        }
    if "merit" in q and any(word in q for word in ["calculate", "calculated", "determined"]):
        return {
            "answer": "Merit is often based on the percentage of obtained marks. Some programs use weighted formulas, such as FSc marks plus test marks. Please ask with the exact program name for the precise merit formula.",
            "sources": [source_item("Admissions_Criteria_Paragraphsupdated.docx", "admission")],
        }
    return None


def answer_admission(question: str) -> Optional[Dict]:
    admissions = load_json("admissions.json", {})
    if is_lms_password_query(question):
        return unavailable_answer("LMS password reset")
    if is_result_awaiting_query(question):
        return {
            "answer": "Sorry, I could not find official information about result-awaiting admission.",
            "sources": [],
        }
    if is_5th_semester_query(question):
        for row in admissions.get("program_criteria", []):
            if "5th semester" in normalize(row.get("text", "")) and "associate degree" in normalize(row.get("text", "")):
                return {
                    "answer": clean_extracted_text(row["text"]),
                    "sources": [source_item(row.get("source"), row.get("category"))],
                }
        return {
            "answer": "Sorry, I could not find official information about 5th semester admission.",
            "sources": [],
        }
    if is_bs_adp_difference_query(question):
        return {
            "answer": (
                "I could not find a direct comparison between BS and ADP programs. "
                "They do state that students holding AD (Associate Degree), BA, BSc, or equivalent are eligible for admission in the 5th semester."
            ),
            "sources": [source_item("Admissions_Criteria_Paragraphsupdated.docx", "admission")],
        }
    if is_admission_procedure_query(question):
        procedure = admissions.get("procedure")
        if not procedure:
            return None
        steps = procedure.get("steps", [])
        # Keep heading plus actual steps; no random program criteria.
        answer_lines = []
        for step in steps:
            if step.lower() == "admission procedure":
                continue
            cleaned = clean_extracted_text(step)
            if cleaned:
                answer_lines.append(f"• {cleaned}")
        return {
            "answer": "Admission procedure:\n" + "\n".join(answer_lines[:10]),
            "sources": [source_item(procedure.get("source"), procedure.get("category"))],
        }
    if is_broad_admission_criteria_query(question):
        return {
            "answer": "Eligibility criteria vary by program. Please specify the exact program name, for example: BS Computer Science, BS Chemistry, or Doctor of Physical Therapy.",
            "sources": [],
        }
    if "calendar" in normalize(question):
        return {
            "answer": "I could not extract a reliable date-wise academic calendar summary yet.",
            "sources": [source_item("IUB Academic Calender.docx", "about university")],
        }
    followup = answer_admission_followups(question)
    if followup:
        return followup
    if any(word in normalize(question) for word in ["admission", "criteria", "eligibility", "requirement", "requirements"]):
        direct = direct_program_criteria_answer(question)
        if direct:
            return direct
        rows = find_program_criteria_rows(question, admissions)
        if rows:
            return format_admission_rows(rows)
    return None


def answer_about_university(question: str) -> Optional[Dict]:
    q = normalize(question)
    if q not in {"what is iub", "what is the islamia university", "what is islamia university", "about iub", "tell me about iub", "where is iub located", "where is iub"}:
        return None
    history = find_cleaned_document("history.docx")
    if not history:
        return None
    if "where" in q:
        return {
            "answer": "The Islamia University of Bahawalpur is located in Bahawalpur. Abbasia Campus is in the city, and Baghdad-ul-Jadeed Campus is on Hasilpur Road about eight kilometers from the city center.",
            "sources": [source_item("Abbasia Campus.docx", "campuses"), source_item("Baghdad-ul-Jadeed Campus.docx", "campuses")],
        }
    return {
        "answer": (
            "IUB stands for The Islamia University of Bahawalpur. "
            "its roots go back to Jamia Abbasia, established in Bahawalpur in 1925, and it developed into "
            "The Islamia University of Bahawalpur."
        ),
        "sources": [source_item(history.get("source"), history.get("category"))],
    }


def answer_identity(question: str) -> Optional[Dict]:
    q = normalize(question)
    if q in {"who are you", "what are you", "you are a chatbot", "are you chatbot", "are you a chatbot"}:
        return {
            "answer": "I am the IUB Offline RAG Chatbot, an AI assistant for answering questions about IUB admissions, fees, departments, faculties, hostels, scholarships, campuses, contacts, and related university information.",
            "sources": [],
        }
    return None


def answer_abbreviation(question: str) -> Optional[Dict]:
    q = normalize(question)
    meanings = {
        "cs": "CS refers to Computer Science. In IUB admission data, BS Computer Science is listed under computing-related programs.",
        "ai": "AI refers to Artificial Intelligence. In IUB admission data, BS Artificial Intelligence is listed under computing-related programs.",
        "se": "SE refers to Software Engineering. In IUB admission data, BS Software Engineering is listed under computing-related programs.",
        "it": "IT refers to Information Technology. In IUB admission data, BS Information Technology is listed under computing-related programs.",
        "ds": "DS refers to Data Science. In IUB admission data, BS Data Science is listed under computing-related programs.",
        "is": "IS refers to Information Systems. In IUB admission data, BS Information Systems is listed with computing-related programs.",
        "bscs": "BSCS refers to BS Computer Science.",
        "bsai": "BSAI refers to BS Artificial Intelligence.",
        "bsse": "BSSE refers to BS Software Engineering.",
        "bsit": "BSIT refers to BS Information Technology.",
        "bsds": "BSDS refers to BS Data Science.",
    }
    for key, value in meanings.items():
        if q in {f"what is {key}", key}:
            return {"answer": value, "sources": [source_item("Admissions_Criteria_Paragraphsupdated.docx", "admission")]}
    return None


def answer_abbreviation_comparison(question: str) -> Optional[Dict]:
    q = normalize(question)
    if not ("difference" in q and all(term in q for term in ["cs", "it", "ai", "se", "ds", "is"])):
        return None
    return {
        "answer": (
            "These abbreviations refer to computing fields: "
            "CS means Computer Science, IT means Information Technology, AI means Artificial Intelligence, "
            "SE means Software Engineering, DS means Data Science, and IS means Information Systems. "
            "For exact admission criteria or fee, ask about one program at a time."
        ),
        "sources": [source_item("Admissions_Criteria_Paragraphsupdated.docx", "admission")],
    }


def answer_doit(question: str) -> Optional[Dict]:
    q = normalize(question)
    if "doit" not in q and "directorate of information technology" not in q and "it services" not in q:
        return None
    if ("director" in q or "who" in q) and "it services" not in q:
        return None
    return {
        "answer": "DoIT means the Directorate of Information Technology. It supports digital transformation, academic services, research support, governance, and technology services at IUB.",
        "sources": [source_item("faculty data.docx", "faculty and departments")],
    }


def answer_programs_overview(question: str) -> Optional[Dict]:
    q = normalize(question)
    if not (
        "program" in q
        and any(word in q for word in ["offered", "offer", "available", "programs"])
        and ("iub" in q or "university" in q)
        and not any(word in q for word in ["department", "faculty", "fee", "criteria", "eligibility"])
    ):
        return None
    faculties = load_json("faculties.json", [])
    if not faculties:
        return None
    names = [fac["faculty"] for fac in faculties if fac.get("faculty")]
    lines = [
        "IUB offers programs across multiple faculties, including:",
        *[f"• {name}" for name in names[:14]],
        "Please ask for a specific faculty, department, campus, or program for an exact program list.",
    ]
    return {
        "answer": "\n".join(lines),
        "sources": [source_item("faculties with department.pdf", "faculty and departments")],
    }


def answer_faculty(question: str) -> Optional[Dict]:
    q = normalize(question)
    if "faculty" not in q:
        return None
    faculties = load_json("faculties.json", [])
    best = None
    best_score = 0
    q_tokens = tokens(question)
    for fac in faculties:
        f_tokens = tokens(fac.get("faculty", ""))
        score = 0
        if fac.get("faculty_norm") and fac["faculty_norm"] in q:
            score += 100
        score += sum(1 for t in q_tokens if t in f_tokens) * 15
        # Also allow content-word loose match, but not just the word faculty
        if score > best_score:
            best_score = score
            best = fac
    if not best or best_score < 15:
        return None
    lines = [f"{best['faculty']} includes the following departments/institutes/units:"]
    for unit in best.get("units", []):
        programs = unit.get("programs", [])
        if programs:
            program_text = ", ".join(clean_extracted_text(p) for p in programs)
            lines.append(f"• {clean_extracted_text(unit['name'])}: {program_text}")
        else:
            lines.append(f"• {clean_extracted_text(unit['name'])}")
    dean = find_dean_for_faculty(best.get("faculty", ""))
    if dean:
        lines.append(f"\nDean/Head: {dean['name']} - {dean['designation']}.")
    else:
        lines.append("\nDean/Head information for this faculty is not clearly available.")
    return {"answer": "\n".join(lines), "sources": [source_item(best.get("source"), best.get("category"))]}


def find_dean_for_faculty(faculty: str) -> Optional[Dict]:
    people = load_json("people.json", [])
    faculty_norm = normalize(faculty)
    key = faculty_norm.replace("faculty of", "").strip()
    for person in people:
        d = person.get("designation_norm", "")
        if "dean" not in d:
            continue
        # Strict: designation must include exact faculty or full faculty key, not just one common word.
        if faculty_norm in d or (len(key) > 8 and key in d):
            return person
    return None


def answer_department(question: str) -> Optional[Dict]:
    q = normalize(question)
    if "department" not in q and "institute" not in q and "unit" not in q:
        return None
    faculties = load_json("faculties.json", [])
    q_tokens = tokens(question)
    best = None
    best_score = 0
    for fac in faculties:
        for unit in fac.get("units", []):
            u_norm = unit.get("name_norm") or normalize(unit.get("name", ""))
            u_tokens = tokens(unit.get("name", ""))
            score = 0
            if u_norm and u_norm in q:
                score += 100
            score += sum(1 for t in q_tokens if t in u_tokens) * 20
            if score > best_score:
                best_score = score
                best = (fac, unit)
    if not best or best_score < 20:
        return None
    fac, unit = best
    programs = unit.get("programs", [])
    lines = [f"{clean_extracted_text(unit['name'])} is listed under {fac['faculty']}."]
    if programs:
        lines.append("Available programs:")
        lines.extend([f"• {clean_extracted_text(p)}" for p in programs])
    return {"answer": "\n".join(lines), "sources": [source_item(fac.get("source"), fac.get("category"))]}


def answer_computing_program_question(question: str) -> Optional[Dict]:
    q = normalize(question)
    if "faculty of computing" not in q and "computing" not in q:
        return None
    if not any(word in q for word in ["program", "programs", "department", "departments", "included"]):
        return None
    return answer_faculty("Faculty of Computing")


def answer_academic_policy_unavailable(question: str) -> Optional[Dict]:
    q = normalize(question)
    academic_terms = [
        "semester system", "how many semesters", "passing marks", "cgpa", "gpa",
        "minimum cgpa", "fail a subject", "repeat course", "improvement exam",
        "improve my grade", "attendance requirement", "attendance short",
        "absences", "midterm", "final exam", "grading system",
    ]
    if any(term in q for term in academic_terms):
        return unavailable_answer("academic policy")
    return None


def answer_program_department_mapping(question: str) -> Optional[Dict]:
    q = normalize(question)
    mappings = {
        "bscs": ("BS Computer Science", "Department of Computer Science"),
        "bs computer science": ("BS Computer Science", "Department of Computer Science"),
        "bs artificial intelligence": ("BS Artificial Intelligence", "Department of Artificial Intelligence"),
        "bs data science": ("BS Data Science", "Department of Data Science"),
        "bs software engineering": ("BS Software Engineering", "Department of Software Engineering"),
        "bs information technology": ("BS Information Technology", "Department of Information Technology"),
    }
    if "which department" not in q and "offers" not in q:
        return None
    for key, (program, department) in mappings.items():
        if key in q:
            return {
                "answer": f"{program} is listed with the {department}.",
                "sources": [source_item("Admissions_Criteria_Paragraphsupdated.docx", "admission")],
            }
    return None


def answer_people(question: str) -> Optional[Dict]:
    q = normalize(question)
    if not any(x in q for x in ["who is", "head", "director", "vc", "vice chancellor", "dean", "chairman", "chairperson", "officer"]):
        return None
    people = load_json("people.json", [])

    # Exact role shortcuts based on query wording, not hardcoded university facts.
    if "vc" in q or "vice chancellor" in q:
        exact = [p for p in people if "vice chancellor" in p.get("designation_norm", "")]
        if exact:
            top = exact[0]
            return {"answer": f"{top['name']} serves as {top['designation']}.", "sources": [source_item(top.get("source"), top.get("category"))]}

    if "director it" in q or "director of it" in q or "head of it" in q:
        exact = [p for p in people if p.get("designation_norm", "") == "director it" or " director it" in p.get("designation_norm", "")]
        if exact:
            top = exact[0]
            return {"answer": f"{top['name']} serves as {top['designation']}.", "sources": [source_item(top.get("source"), top.get("category"))]}

    if "head" in q and any(term in q for term in ["computer science", "artificial intelligence", "software engineering", "information technology", "data science", "information security"]):
        return {
            "answer": "Head/Chairperson information for this department is not clearly available.",
            "sources": [source_item("faculty data.docx", "faculty and departments")],
        }

    q_tokens = tokens(question)
    scored = []
    for person in people:
        d = person.get("designation_norm", "")
        n = person.get("name_norm", "")
        score = 0
        for t in q_tokens:
            if t in d:
                score += 12
            if t in n:
                score += 8
        if score:
            scored.append((score, person))
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    top_score, top = scored[0]
    if top_score < 12:
        return None
    return {"answer": f"{top['name']} serves as {top['designation']}.", "sources": [source_item(top.get("source"), top.get("category"))]}


def answer_campuses(question: str) -> Optional[Dict]:
    q = normalize(question)
    if "hostel" in q or "hostels" in q:
        return None
    if "campus" not in q and "campuses" not in q:
        return None
    campuses = load_json("campuses.json", [])
    for campus in campuses:
        name_norm = normalize(campus.get("name", ""))
        short_name = name_norm.replace("sub-campus", "campus")
        if name_norm and (name_norm in q or short_name in q):
            if any(word in q for word in ["program", "programs", "offered", "offer"]):
                if "khawaja fareed" in name_norm:
                    return {
                        "answer": "I could not find a program list for Khawaja Fareed Campus. The campus information mentions the Faculty of Pharmacy and the Faculty of Medicine and Allied Health Sciences there.",
                        "sources": [source_item(campus.get("source"), campus.get("category"))],
                    }
                return unavailable_answer(f"programs offered at {campus.get('name')}")
            if "faculty" in q or "faculties" in q:
                text_norm = normalize(campus.get("text", ""))
                if "faculty of pharmacy" in text_norm and "faculty of medicine and allied health sciences" in text_norm:
                    return {
                        "answer": f"{campus.get('name')} has the Faculty of Pharmacy and the Faculty of Medicine and Allied Health Sciences.",
                        "sources": [source_item(campus.get("source"), campus.get("category"))],
                    }
            text = clean_extracted_text(campus.get("text", ""))
            if not text:
                break
            summary = text.split(". ")[0]
            if len(summary.split()) < 12 and ". " in text:
                summary = ". ".join(text.split(". ")[:2])
            words = summary.split()
            midpoint = len(words) // 2
            if midpoint and words[:midpoint] == words[midpoint:midpoint * 2]:
                summary = " ".join(words[midpoint:])
            campus_name = campus.get("name", "")
            doubled = f"{campus_name} {campus_name}"
            if campus_name and summary.startswith(doubled):
                summary = campus_name + summary[len(doubled):]
            established_prefix = f"{campus_name} The Islamia University of Bahawalpur established {campus_name}"
            if campus_name and summary.startswith(established_prefix):
                summary = campus_name + " was established" + summary[len(established_prefix):]
            return {
                "answer": summary.strip().rstrip(".") + ".",
                "sources": [source_item(campus.get("source"), campus.get("category"))],
            }
    if not any(x in q for x in ["what", "list", "which", "campuses", "have"]):
        return None
    if not campuses:
        return None
    lines = ["IUB campuses include:"]
    for c in campuses:
        lines.append(f"• {c['name']}")
    return {"answer": "\n".join(lines), "sources": format_sources(campuses)}


def answer_office_location(question: str) -> Optional[Dict]:
    q = normalize(question)
    office_map = {
        "admission office": "Admission Cell",
        "examination office": "Examination Division",
        "registrar office": "Registrar Office",
        "treasurer office": "Accounts Division",
        "student affairs office": "Directorate of Students Affairs",
    }
    for asked, office in office_map.items():
        if asked in q:
            if asked == "student affairs office":
                return unavailable_answer("the location of the student affairs office")
            return {
                "answer": f"{office} is at Abbasia Campus.",
                "sources": [source_item("Abbasia Campus.docx", "campuses")],
            }
    if "official website" in q:
        return {"answer": "The university website is www.iub.edu.pk.", "sources": [source_item("how to apply for admission.docx", "admission")]}
    return None


def answer_library_unavailable(question: str) -> Optional[Dict]:
    q = normalize(question)
    if any(term in q for term in ["books can", "keep a book", "late return", "library timing", "library card", "digital library", "research papers", "central library"]):
        return unavailable_answer("library services")
    return None


def answer_scholarships(question: str) -> Optional[Dict]:
    q = normalize(question)
    if "scholarship" not in q and "beef" not in q and "peef" not in q:
        return None
    scholarships = load_json("scholarships.json", [])
    if not scholarships:
        return None
    if any(word in q for word in ["info", "information", "available", "list", "what scholarships"]):
        lines = ["Scholarships include:"]
        for s in scholarships:
            lines.append(f"• {s['name']}")
        return {"answer": "\n".join(lines), "sources": format_sources(scholarships)}
    if "contact" in q or "who" in q:
        return unavailable_answer("scholarship contact information")
    # Specific scholarship question: return relevant lines from matching doc.
    q_toks = set(tokens(question))
    best = None
    best_score = 0
    for s in scholarships:
        score = sum(1 for t in q_toks if t in normalize(s.get("name", "")))
        if score > best_score:
            best_score = score
            best = s
    if best and best_score > 0 and not any(x in q for x in ["offers", "available", "list", "what scholarships"]):
        if (
            "punjab" in q
            and ("beef" in normalize(best.get("name", "")) or "balochistan education endowment" in normalize(best.get("text", "")))
        ):
            answer = (
                "BEEF is for talented and needy students of "
                "Balochistan. I could not find official information that Punjab province students are eligible for BEEF. "
                "Punjab students should check Punjab-based scholarship options such as PEEF if available."
            )
            return {"answer": answer, "sources": [source_item(best.get("source"), best.get("category"))]}
        sentences = [x.strip() for x in re.split(r"(?<=\.)\s+|\n+", best.get("text", "")) if x.strip()]
        wanted = [s for s in sentences if any(t in normalize(s) for t in q_toks) or any(w in normalize(s) for w in ["eligible", "eligibility", "province", "balochistan", "punjab", "apply"])]
        if not wanted:
            wanted = sentences[:4]
        answer = f"For {best['name']}:\n" + "\n".join(f"• {x}" for x in wanted[:5])
        if "punjab" in q and "balochistan" in normalize(best.get("text", "")) and "punjab" not in normalize(best.get("text", "")):
            answer += "\nI could not find official information that Punjab province students are eligible for this scholarship."
        return {"answer": answer, "sources": [source_item(best.get("source"), best.get("category"))]}
    # List scholarship docs
    lines = ["Scholarships include:"]
    for s in scholarships:
        lines.append(f"• {s['name']}")
    return {"answer": "\n".join(lines), "sources": format_sources(scholarships)}


def answer_hostels(question: str) -> Optional[Dict]:
    q = normalize(question)
    if "hostel" not in q and "hostels" not in q and not ("hall" in q and any(name in q for name in ["fatima", "ayesha", "khadija", "amna", "zainab", "halima", "umar", "ali", "ahmad", "usman", "rabia", "abu bakar", "iqbal"])):
        return None
    if is_hostel_fee_query(question):
        return {"answer": FALLBACK_ANSWER, "sources": []}
    hostels = load_json("hostels.json", {})
    if not hostels:
        return None
    if any(phrase in q for phrase in ["how apply", "how can apply", "apply hostel", "apply for hostel", "hostel admission", "hostel form"]):
        return {
            "answer": (
                "Hostel information includes facilities, campus-wise hostels, and administration, "
                "but it does not provide a hostel application procedure."
            ),
            "sources": [source_item(hostels.get("source"), hostels.get("category"))],
        }
    if any(word in q for word in ["charge", "charges", "fee", "timing", "rules", "warden", "office", "documents", "merit", "complain", "contact"]):
        return unavailable_answer("that hostel procedure/detail")
    if "fatima" in q and "hall" in q:
        return {
            "answer": "Fatima-tuz-Zahra Hall is a girls' hostel located at Baghdad-ul-Jadeed Campus.",
            "sources": [source_item(hostels.get("source"), hostels.get("category"))],
        }
    if "facilit" in q:
        facilities = [
            "cafeteria", "dining hall", "common room with indoor games", "computer labs",
            "reading room", "library", "mosque", "sports club", "gym", "laundry rooms",
            "gardens", "study parks", "electricity connection points", "high speed internet",
            "separate sitting areas",
        ]
        return {
            "answer": "Hostel facilities include:\n" + "\n".join(f"• {item}" for item in facilities),
            "sources": [source_item(hostels.get("source"), hostels.get("category"))],
        }
    sections = hostels.get("campus_sections", [])
    q_toks = set(tokens(question))
    campus_words = [t for t in q_toks if t in {"baghdad", "baghdad-ul-jadeed", "abbasia", "bahawalnagar", "rahim", "khan"}]
    relevant = []
    for sent in sections:
        s_norm = normalize(sent)
        if campus_words:
            if any(t in s_norm for t in campus_words):
                relevant.append(sent)
        elif any(t in s_norm for t in q_toks):
            relevant.append(sent)
    if not relevant:
        relevant = sections[:4]
    return {
        "answer": "\n".join(f"• {line}" for line in relevant[:5]),
        "sources": [source_item(hostels.get("source"), hostels.get("category"))],
    }


def answer_transport(question: str) -> Optional[Dict]:
    q = normalize(question)
    if not any(word in q for word in ["transport", "bus", "route", "routes"]):
        return None
    transport = find_cleaned_document("transport.txt")
    if not transport:
        return None
    answer = (
        "The transport schedule is effective from April 20, 2026 and covers services between "
        "Abbasia Campus, Baghdad-ul-Jadeed Campus, and Khwaja Fareed Campus. It includes morning, afternoon, evening, "
        "and Saturday routes. For route help, the document lists Morning Shift contacts 0349-4417157 and 0306-8153213, "
        "Evening Shift contacts 0300-8742694 and 0308-2511630, and WhatsApp complaints at 0300-6809094."
    )
    return {
        "answer": answer,
        "sources": [source_item(transport.get("source"), transport.get("category"))],
    }


def answer_contact(question: str) -> Optional[Dict]:
    q = normalize(question)
    if not any(word in q for word in ["contact", "phone", "email", "helpline", "address", "telephone"]):
        return None
    contacts = find_cleaned_document("contact .docx")
    text = contacts.get("text") if contacts else None
    if not text:
        return None
    return {
        "answer": text,
        "sources": [source_item(contacts.get("source"), contacts.get("category"))],
    }


def answer_operational_unavailable(question: str) -> Optional[Dict]:
    q = normalize(question)
    if not is_operational_workflow_query(q):
        return None
    if "lms" in q:
        return unavailable_answer("LMS procedure")
    if "portal" in q:
        return unavailable_answer("portal procedure")
    if any(word in q for word in ["date sheet", "roll number", "rechecking", "improvement", "repeat", "degree", "transcript", "result", "grading"]):
        return unavailable_answer("examination procedure")
    if "library" in q:
        return unavailable_answer("library services")
    if any(word in q for word in ["attendance", "marks", "course", "award", "sessional", "timetable"]):
        return unavailable_answer("academic management workflow")
    if any(word in q for word in ["leave", "joining", "experience certificate", "noc", "promotion", "hr"]):
        return unavailable_answer("HR procedure")
    if any(word in q for word in ["research", "oric", "publication", "conference", "hec-recognized journals", "hec recognized journals"]):
        return unavailable_answer("research/ORIC procedure")
    if any(word in q for word in ["wifi", "wi-fi", "email", "online classes", "internet"]):
        return unavailable_answer("IT service procedure")
    return unavailable_answer("this procedure")


def answer_english_department(question: str) -> Optional[Dict]:
    q = normalize(question)
    if "department" not in q or "english" not in q:
        return None
    faculties = load_json("faculties.json", [])
    for fac in faculties:
        units = []
        for unit in fac.get("units", []):
            if "english" in normalize(unit.get("name", "")):
                units.append(unit)
        if not units:
            continue
        lines = [f"English-related units are listed under {fac['faculty']}:"]
        for unit in units:
            programs = unit.get("programs", [])
            if programs:
                lines.append(f"• {unit['name']}: {', '.join(programs)}")
            else:
                lines.append(f"• {unit['name']}")
        return {"answer": "\n".join(lines), "sources": [source_item(fac.get("source"), fac.get("category"))]}
    return None


def answer_from_kb(question: str, last_question: str = "") -> Optional[Dict]:
    if is_greeting(question):
        return {"answer": "Hello! I can answer questions about IUB admissions, fees, departments, faculties, hostels, scholarships, contacts, and university information.", "sources": []}

    # Order matters: specific safe handlers before broad RAG.
    for handler in [
        answer_identity,
        answer_about_university,
        answer_abbreviation,
        answer_abbreviation_comparison,
        answer_doit,
        answer_programs_overview,
        lambda q: answer_admission(q),
        lambda q: answer_fee(q, last_question),
        answer_academic_policy_unavailable,
        answer_office_location,
        answer_computing_program_question,
        answer_program_department_mapping,
        answer_faculty,
        answer_english_department,
        answer_department,
        answer_people,
        answer_scholarships,
        answer_hostels,
        answer_library_unavailable,
        answer_campuses,
        answer_transport,
        answer_contact,
        answer_operational_unavailable,
    ]:
        result = handler(question)
        if result is not None:
            return result
    return None
