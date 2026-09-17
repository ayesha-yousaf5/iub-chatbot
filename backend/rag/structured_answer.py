import re
from typing import Dict, Optional

from rag.structured_kb import (
    normalize,
    detect_program,
    detect_group,
    find_fee_records_safe,
    find_person_by_designation,
    find_person_by_name,
    get_campus_list,
    get_scholarship_list,
    find_admission_context,
    get_hostel_facilities_text,
    get_contact_text,
    detect_faculty,
    FACULTY_DATA,
    find_faculty_dean,
    detect_department,
    detect_hostel_campus,
)


FALLBACK_ANSWER = "Sorry, I could not find official information about this in the available university documents."
NEED_PROGRAM_ANSWER = "Please specify the program name so I can answer accurately."


def source_item(source: str, category: str, score: str = "structured"):
    return {"source": source, "category": category, "score": score}


def is_greeting(q: str) -> bool:
    return q in {"hi", "hello", "hey", "salam", "assalam o alaikum", "assalamu alaikum"}


def is_fee_query(q: str) -> bool:
    return any(word in q for word in ["fee", "fees", "dues", "cost", "tuition", "challan", "charges"])


def is_admission_query(q: str) -> bool:
    return any(word in q for word in ["admission", "criteria", "eligibility", "requirement", "requirements", "apply", "bachelor", "bachelors"])


def is_how_to_apply_query(q: str) -> bool:
    return any(phrase in q for phrase in [
        "how to apply",
        "method to apply",
        "full method to apply",
        "apply for admission",
        "procedure for admission",
        "admission procedure",
        "how can i apply",
    ])


def is_broad_bs_admission_query(q: str) -> bool:
    broad_phrases = [
        "eligibility criteria for bs admission",
        "criteria for bs admission",
        "bs admission",
        "bachelor admission",
        "bachelors admission",
        "admission in bachelors",
        "admission in bachelor",
        "admission for bachelors",
        "admission for bachelor",
    ]
    return any(phrase in q for phrase in broad_phrases)


def is_beef_specific_query(q: str) -> bool:
    return "beef" in q or "balochistan education endowment" in q


def is_person_query(q: str) -> bool:
    return ("who is" in q) or any(phrase in q for phrase in ["director it", "vice chancellor", " vc ", "head of", "registrar", "treasurer", "controller", "chief security"])


def is_doit_overview_query(q: str) -> bool:
    return any(phrase in q for phrase in ["tell about directorate of information technology", "explain directorate of information technology", "what is directorate of information technology", "who is directorate of information technology"])


def is_campus_list_query(q: str) -> bool:
    return any(phrase in q for phrase in ["what campuses", "campuses does iub have", "list campuses", "iub campuses", "campuses of iub", "all campuses"])


def is_scholarship_list_query(q: str) -> bool:
    return "scholarship" in q and any(word in q for word in ["available", "list", "what scholarships", "all scholarships"])


def is_hostel_query(q: str) -> bool:
    return "hostel" in q or "hostels" in q or "residential" in q


def is_contact_query(q: str) -> bool:
    return any(word in q for word in ["contact", "phone", "email", "helpline", "admission office"])


def is_faculty_query(q: str) -> bool:
    return "faculty" in q


def is_department_query(q: str) -> bool:
    return "department" in q or "institute" in q or "college" in q


def wants_tuition_only(q: str) -> bool:
    return "tuition" in q and not any(word in q for word in ["full", "total", "complete", "overall", "1st semester", "semester"])


def format_fee_answer(program: str, records, question: str) -> str:
    q = normalize(question)
    if not records:
        return FALLBACK_ANSWER
    if len(records) == 1:
        r = records[0]
        if wants_tuition_only(q):
            return f"The tuition fee for {r['program']} {r['group']} is {r['tuition_fee']}."
        return (
            f"For {r['program']} {r['group']}:\n"
            f"• Tuition fee: {r['tuition_fee']}\n"
            f"• Other dues: {r['other_dues']}\n"
            f"• Total fee for 1st semester: {r['total_1st_semester']}\n"
            f"• Total fee for 2nd and other semesters: {r['total_other_semesters']}"
        )
    lines = [f"The available fee records for {program} are:"]
    for r in records:
        if wants_tuition_only(q):
            lines.append(f"• {r['group']}: tuition fee {r['tuition_fee']}")
        else:
            lines.append(f"• {r['group']}: tuition fee {r['tuition_fee']}, other dues {r['other_dues']}, 1st semester total {r['total_1st_semester']}, 2nd and other semesters total {r['total_other_semesters']}")
    return "\n".join(lines)


def answer_fee_query(question: str, memory: Optional[Dict] = None):
    q = normalize(question)
    if "hostel" in q or "living" in q:
        return {"answer": FALLBACK_ANSWER, "sources": [source_item("residential and hostel facilities.docx", "hostels")], "memory_update": {"last_topic": "hostels"}}
    group = detect_group(question)
    program = detect_program(question)
    if not program and memory and group and memory.get("last_program"):
        program = memory["last_program"]
    if not program:
        return {"answer": NEED_PROGRAM_ANSWER, "sources": [], "memory_update": {}}
    records = find_fee_records_safe(program, group)
    if not records:
        return {"answer": FALLBACK_ANSWER, "sources": [source_item("Revised fee.docx", "fees")], "memory_update": {"last_program": program, "last_topic": "fees"}}
    return {"answer": format_fee_answer(program, records, question), "sources": [source_item("Revised fee.docx", "fees")], "memory_update": {"last_program": program, "last_topic": "fees"}}


def answer_person_query(question: str):
    q = normalize(question)
    people = []
    if "who is" in q and not any(word in q for word in ["director", "vc", "vice chancellor", "head of", "registrar", "treasurer", "controller", "chief"]):
        people = find_person_by_name(question)
    if not people:
        people = find_person_by_designation(question)
    if not people:
        return None
    p = people[0]
    return {"answer": f"{p['name']} serves as {p['designation']}.", "sources": [source_item(p["source"], p["category"])], "memory_update": {"last_person": p["name"], "last_topic": "person"}}


def answer_campuses_query(question: str):
    campuses = get_campus_list()
    if not campuses:
        return None
    preferred_order = ["Abbasia Campus", "Baghdad-ul-Jadeed Campus", "Bahawalnagar Sub-Campus", "Khawaja Fareed Campus", "Liaquatpur Sub-Campus", "Rahim Yar Khan Sub-Campus"]
    found = {c["name"]: c for c in campuses}
    ordered = [name for name in preferred_order if name in found]
    ordered.extend([c["name"] for c in campuses if c["name"] not in ordered])
    answer = "The available IUB campus documents include:\n" + "\n".join([f"• {name}" for name in ordered])
    return {"answer": answer, "sources": [source_item("campus documents", "campuses")], "memory_update": {"last_topic": "campuses"}}


def answer_scholarship_query(question: str):
    scholarships = get_scholarship_list()
    if not scholarships:
        return None
    answer = "The available scholarship documents include:\n" + "\n".join([f"• {item['name']}" for item in scholarships])
    return {"answer": answer, "sources": [source_item("scholarship documents", "scholarships")], "memory_update": {"last_topic": "scholarships"}}


def answer_how_to_apply_query(question: str):
    answer = (
        "Admission procedure for Bachelor and Master classes at IUB:\n"
        "• Register on the university website www.iub.edu.pk by filling the registration form.\n"
        "• After registration, fill the admission application form carefully with correct information.\n"
        "• After submitting a valid application form, print the system-generated challan form.\n"
        "• Deposit the prescribed admission processing fee through the auto-generated challan in the nearest HBL branch.\n"
        "• For another program or department, submit a separate application form and separate challan.\n"
        "• Login with registration information if any information needs to be updated.\n"
        "• Check application status online.\n"
        "• If your name appears in a merit list, appear in person within the due time with all original documents before the respective department admission committee."
    )
    return {"answer": answer, "sources": [source_item("how to apply for admission.docx", "admission")], "memory_update": {"last_topic": "admission"}}


def answer_broad_bs_admission_query(question: str):
    answer = (
        "For BS/Bachelor admission at IUB, eligibility depends on the specific program. In the available admission criteria, many BS programs require FA/FSc or equivalent, while computing programs may require ICS/FSc/I.Com or FA with relevant subjects such as Computer Science, Statistics, Economics, Mathematics, Physics, or Commerce. Some programs also require relevant admission tests such as IUB Test, NAT, ECAT, MCAT, HEC test, or LAT, depending on the program. Merit is generally based on the percentage of obtained marks.\n\n"
        "Please tell me the exact program name, for example BS Computer Science, BS Chemistry, BS Education, DPT, Pharm-D, or BS Artificial Intelligence, so I can give the exact eligibility criteria."
    )
    return {"answer": answer, "sources": [source_item("Admissions_Criteria_Paragraphsupdated.docx", "admission")], "memory_update": {"last_topic": "admission"}}


def answer_beef_query(question: str):
    q = normalize(question)
    if "punjab" in q:
        answer = (
            "According to the available BEEF document, BEEF is the Balochistan Education Endowment Fund, an initiative of the Government of Balochistan for talented and needy youth/students of Balochistan. The document does not state eligibility for students belonging to Punjab province. For Punjab students, you should check Punjab-based scholarship options such as PEEF if available."
        )
    else:
        answer = (
            "BEEF stands for Balochistan Education Endowment Fund. It is an initiative of the Government of Balochistan to provide need- and merit-based scholarships to talented and needy students of Balochistan. Applications for Categories A and B are accepted through the head of the institution by post, and the scholarship form is also available on the BEEF website."
        )
    return {"answer": answer, "sources": [source_item("BEEF Scholarship Program.docx", "scholarships")], "memory_update": {"last_topic": "scholarships"}}


def answer_admission_query(question: str, memory: Optional[Dict] = None):
    q = normalize(question)
    program = detect_program(question)

    # Use previous program only for clear follow-ups like "what about eligibility".
    # Do not use memory for broad questions such as "how to apply" or "BS admission".
    if not program and memory and memory.get("last_program") and not is_broad_bs_admission_query(q) and not is_how_to_apply_query(q):
        program = memory["last_program"]

    if not program:
        return answer_broad_bs_admission_query(question)

    context = find_admission_context(program)
    if not context:
        return None
    return {"answer": context["text"], "sources": [source_item(context["source"], context["category"])], "memory_update": {"last_program": program, "last_topic": "admission"}}


def answer_faculty_query(question: str):
    faculty = detect_faculty(question)
    if not faculty:
        return None
    info = FACULTY_DATA[faculty]
    dean = find_faculty_dean(faculty)
    lines = [f"{faculty} includes the following departments/institutes/units:"]
    for unit, programs in info["units"].items():
        program_text = "; ".join(programs[:5])
        if len(programs) > 5:
            program_text += "; ..."
        lines.append(f"• {unit}: {program_text}")
    if dean:
        lines.append(f"\nDean/Head mentioned in available documents: {dean['name']} — {dean['designation']}.")
    else:
        lines.append("\nDean/Head information for this faculty is not clearly available in the provided documents.")
    return {"answer": "\n".join(lines), "sources": [source_item("faculties with department.pdf", "faculty and departments")], "memory_update": {"last_faculty": faculty, "last_topic": "faculty"}}


def answer_department_query(question: str):
    dep = detect_department(question)
    if not dep:
        return None
    lines = [f"{dep['unit']} is listed under {dep['faculty']}."]
    if dep["programs"]:
        lines.append("Programs mentioned in the available faculty document:")
        lines.extend([f"• {p}" for p in dep["programs"]])
    lines.append("Head/Chairperson information is not clearly available in the structured faculty list; if present, it may be in the detailed faculty data document.")
    return {"answer": "\n".join(lines), "sources": [source_item("faculties with department.pdf", "faculty and departments")], "memory_update": {"last_department": dep['unit'], "last_faculty": dep['faculty'], "last_topic": "department"}}


def answer_hostel_query(question: str):
    q = normalize(question)
    campus_hostels = detect_hostel_campus(question)
    if campus_hostels:
        answer = f"Hostels mentioned for {campus_hostels['campus']}:\n" + "\n".join([f"• {item}" for item in campus_hostels["items"]])
        return {"answer": answer, "sources": [source_item("residential and hostel facilities.docx", "hostels")], "memory_update": {"last_topic": "hostels"}}
    if not any(word in q for word in ["facility", "facilities", "available", "how many", "count", "tell about"]):
        return None
    info = get_hostel_facilities_text()
    if not info:
        return None
    text = info["text"]
    if "how many" in q or "count" in q:
        match = re.search(r"Sixteen hostels[^.]+", text, flags=re.IGNORECASE)
        answer = match.group(0).strip() if match else FALLBACK_ANSWER
    else:
        answer = "Hostel facilities mentioned in the available documents include:\n" + "\n".join([f"• {item}" for item in ["cafeteria", "dining hall", "common room with indoor games", "computer labs", "reading room", "library", "mosque", "sports club", "gym", "laundry rooms", "study parks", "high speed internet", "separate sitting areas"]])
    return {"answer": answer, "sources": [source_item(info["source"], info["category"])], "memory_update": {"last_topic": "hostels"}}


def answer_contact_query(question: str):
    info = get_contact_text()
    if not info:
        return None
    return {"answer": info["text"], "sources": [source_item(info["source"], info["category"])], "memory_update": {"last_topic": "contact"}}


def answer_doit_overview(question: str):
    return {"answer": "The Directorate of Information Technology is a key unit for digital transformation at The Islamia University of Bahawalpur. It supports academic excellence, research advancement, efficient governance, and modernization of the university's technological services.", "sources": [source_item("faculty data.docx", "faculty and departments")], "memory_update": {"last_topic": "doit"}}


def structured_answer(question: str, memory: Optional[Dict] = None):
    if memory is None:
        memory = {}
    q = normalize(question)
    if not q:
        return None
    if is_greeting(q):
        return {"answer": "Hello! I can answer questions about IUB admissions, fees, departments, faculties, hostels, scholarships, contacts, and university information.", "sources": [], "memory_update": {}}
    if is_doit_overview_query(q):
        return answer_doit_overview(question)
    if is_beef_specific_query(q):
        return answer_beef_query(question)
    if is_how_to_apply_query(q):
        return answer_how_to_apply_query(question)
    if is_broad_bs_admission_query(q):
        return answer_broad_bs_admission_query(question)
    if detect_group(question) and memory.get("last_topic") == "fees":
        return answer_fee_query(question, memory)
    if is_hostel_query(q):
        result = answer_hostel_query(question)
        if result:
            return result
    if is_faculty_query(q):
        result = answer_faculty_query(question)
        if result:
            return result
    if is_department_query(q):
        result = answer_department_query(question)
        if result:
            return result
    if is_fee_query(q):
        return answer_fee_query(question, memory)
    if is_person_query(q):
        result = answer_person_query(question)
        if result:
            return result
    if is_campus_list_query(q):
        return answer_campuses_query(question)
    if is_admission_query(q):
        result = answer_admission_query(question, memory)
        if result:
            return result
    if is_scholarship_list_query(q):
        return answer_scholarship_query(question)
    if is_contact_query(q):
        result = answer_contact_query(question)
        if result:
            return result
    return None
