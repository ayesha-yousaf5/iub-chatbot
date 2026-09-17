import re

from rag.auto_kb import (
    normalize,
    get_admission_procedure,
    find_faculty,
    find_scholarship,
    list_scholarships,
    search_fee_text,
    get_hostel_text,
)

FALLBACK_ANSWER = "Sorry, I could not find official information about this in the available university documents."


def source(source_name, category):
    return [{"source": source_name, "category": category, "score": "data-driven"}]


def is_greeting(q: str):
    return normalize(q) in ["hi", "hello", "hey", "salam", "assalam o alaikum", "assalamu alaikum"]


def wants_admission_procedure(q: str):
    n = normalize(q)
    procedure_words = ["how to apply", "apply for admission", "admission procedure", "method to apply", "full method", "online apply"]
    return any(normalize(w) in n for w in procedure_words)


def is_broad_eligibility(q: str):
    n = normalize(q)
    if "eligibility" not in n and "criteria" not in n:
        return False
    broad_words = ["bs admission", "bachelor admission", "bachelors admission", "undergraduate admission", "admission in bachelors"]
    return any(w in n for w in broad_words)


def wants_scholarship_list(q: str):
    n = normalize(q)
    return "scholarship" in n and any(w in n for w in ["offer", "offers", "available", "list", "what scholarships"])


def wants_fee(q: str):
    n = normalize(q)
    if "hostel" in n:
        return False
    return any(w in n for w in ["fee", "fees", "dues", "tuition", "charges"])


def extract_program_from_fee_question(q: str):
    n = normalize(q)
    n = re.sub(r"\b(what|is|the|of|for|tell|me|about|full|fee|fees|dues|tuition|charges|program)\b", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def wants_faculty_answer(q: str):
    return "faculty" in normalize(q)


def wants_hostel_answer(q: str):
    return "hostel" in normalize(q) or "hostels" in normalize(q)


def answer_admission_procedure():
    data = get_admission_procedure()
    if not data:
        return None

    lines = [line.strip() for line in data["text"].splitlines() if line.strip()]
    useful = []
    for line in lines:
        if line.lower().startswith("admission procedure"):
            continue
        if line.lower().startswith("step") or "candidate" in line.lower() or "applicant" in line.lower():
            useful.append(line)

    if not useful:
        useful = lines[:10]

    answer = "Admission procedure at IUB:\n" + "\n".join(f"• {line}" for line in useful[:10])
    return {"answer": answer, "sources": source(data["source"], data["category"])}


def answer_faculty(q: str):
    name, faculty = find_faculty(q)
    if not faculty:
        return None

    lines = [f"{name} includes the following departments/institutes/units:"]
    for unit, programs in faculty["units"].items():
        if programs:
            lines.append(f"• {unit}: {', '.join(programs)}")
        else:
            lines.append(f"• {unit}")

    lines.append("Dean/Head information is not answered unless it is explicitly present in the available faculty documents.")

    return {
        "answer": "\n".join(lines),
        "sources": source(faculty["source"], faculty["category"]),
    }


def answer_scholarship(q: str):
    if wants_scholarship_list(q):
        names = list_scholarships()
        if not names:
            return None
        return {
            "answer": "The available scholarship documents include:\n" + "\n".join(f"• {name}" for name in names),
            "sources": source("scholarship documents", "scholarships"),
        }

    if "scholarship" not in normalize(q):
        return None

    doc = find_scholarship(q)
    if not doc:
        return None

    text = doc.get("text", "")
    qn = normalize(q)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    keywords = [w for w in qn.split() if len(w) > 3]

    selected = []
    for sent in sentences:
        ns = normalize(sent)
        if any(k in ns for k in keywords) or any(k in ns for k in ["eligibility", "eligible", "balochistan", "punjab", "apply", "criteria"]):
            selected.append(sent.strip())

    if not selected:
        selected = sentences[:3]

    return {
        "answer": "\n".join(f"• {s}" for s in selected[:5]),
        "sources": source(doc.get("source"), doc.get("category")),
    }


def answer_fee(q: str):
    if not wants_fee(q):
        return None

    program = extract_program_from_fee_question(q)
    if not program:
        return {"answer": "Please specify the exact program name so I can search the official fee record accurately.", "sources": []}

    result = search_fee_text(program)
    if not result:
        return {"answer": FALLBACK_ANSWER, "sources": []}

    return {
        "answer": "The matching official fee record says:\n" + result["text"],
        "sources": source(result["source"], result["category"]),
    }


def answer_hostels(q: str):
    if not wants_hostel_answer(q):
        return None

    doc = get_hostel_text()
    if not doc:
        return None

    text = doc.get("text", "")
    qn = normalize(q)

    if "fee" in qn or "charges" in qn:
        return {"answer": FALLBACK_ANSWER, "sources": source(doc.get("source"), doc.get("category"))}

    sentences = re.split(r"(?<=[.!?])\s+", text)
    selected = []
    campus_tokens = []
    for token in ["abbasia", "baghdad", "jadeed", "jaded", "bahawalnagar", "rahim", "ryk"]:
        if token in qn:
            campus_tokens.append(token)

    for sent in sentences:
        ns = normalize(sent)
        if campus_tokens:
            if any(t in ns for t in campus_tokens):
                selected.append(sent.strip())
        elif "hostel" in ns or "boarding" in ns or "facility" in ns:
            selected.append(sent.strip())

    if not selected:
        selected = sentences[:3]

    return {
        "answer": "\n".join(f"• {s}" for s in selected[:4]),
        "sources": source(doc.get("source"), doc.get("category")),
    }


def auto_answer(question: str, last_question: str = ""):
    q = question.strip()
    if not q:
        return None

    if is_greeting(q):
        return {
            "answer": "Hello! I can answer questions about IUB admissions, fees, departments, faculties, hostels, scholarships, contacts, and university information.",
            "sources": [],
        }

    if wants_admission_procedure(q):
        return answer_admission_procedure()

    if is_broad_eligibility(q):
        return {
            "answer": "Please specify the exact BS program name because eligibility criteria can be different for different programs.",
            "sources": [],
        }

    for handler in [answer_faculty, answer_scholarship, answer_fee, answer_hostels]:
        result = handler(q)
        if result:
            return result

    return None
