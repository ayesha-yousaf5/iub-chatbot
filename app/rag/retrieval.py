import os
import json
import re

from rag.vector_store import load_vector_store
from rag.query_processor import expand_abbreviations
from rag.bm25_retriever import bm25_search

VECTOR_DB = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNKS_PATH = os.path.join(BASE_DIR, "processed_data", "chunks.json")


def get_cached_vector_db():
    global VECTOR_DB

    if VECTOR_DB is None:
        VECTOR_DB = load_vector_store()

    return VECTOR_DB


def load_chunks():
    if not os.path.exists(CHUNKS_PATH):
        return []

    with open(CHUNKS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    replacements = {
        "directorate of information technology": "directorate information technology",
        "directorate of it": "directorate information technology",
        "director of it": "director it",
        "director of information technology": "director information technology",
        "doit": "directorate information technology",
        "b.s.": "bs",
        "b s": "bs",
        "c.s.": "cs",
        "c s": "cs",
        "a.i.": "ai",
        "a i": "ai",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def detect_intent(question: str):
    q = normalize_text(expand_abbreviations(question))

    hostel_words = [
        "hostel", "hostels", "residential", "accommodation",
        "boarding", "mess", "dining hall", "common room",
        "warden", "hall council", "student hostels"
    ]

    it_director_words = [
        "director it", "director of it", "directorate of it",
        "directorate information technology", "doit",
        "director information technology",
        "head of information technology",
        "head of it",
        "who is director it",
        "who is director of it"
    ]

    scholarship_words = [
        "scholarship", "scholarships", "financial aid",
        "stipend", "nest", "peef", "gilgit", "baltistan",
        "beef", "diya", "ehsaas", "scotland"
    ]

    fee_words = [
        "fee", "fees", "dues", "challan", "tuition", "payment",
        "semester fee", "fee structure"
    ]

    admission_words = [
        "admission", "criteria", "eligibility", "requirement",
        "requirements", "apply", "merit", "bachelor of science",
        "bs", "fa", "fsc", "ics", "intermediate", "iub test",
        "entry test"
    ]

    contact_words = [
        "contact", "phone", "email", "helpline", "address", "number",
        "telephone", "mobile"
    ]

    about_words = [
        "what is the islamia university", "about iub",
        "about islamia university", "history of iub",
        "history", "governance", "ranking"
    ]

    campus_words = [
        "campus", "campuses", "baghdad", "abbasia",
        "bahawalnagar", "rahim yar khan"
    ]

    facilities_words = [
        "facility", "facilities", "library", "transport",
        "sports", "medical", "cafeteria", "mosque",
        "computer lab", "labs"
    ]

    department_words = [
        "department", "faculty", "program", "programs", "institute",
        "computer science", "artificial intelligence",
        "software engineering", "data science",
        "information technology"
    ]

    # Order matters. Specific intents must come before broad intents.
    if any(word in q for word in hostel_words):
        return "hostels"

    if any(word in q for word in it_director_words):
        return "it_director"

    if any(word in q for word in scholarship_words):
        return "scholarships"

    if any(word in q for word in fee_words):
        return "fees"

    if any(word in q for word in admission_words):
        return "admission"

    if any(word in q for word in contact_words):
        return "contact"

    if any(word in q for word in about_words):
        return "about university"

    if any(word in q for word in campus_words):
        return "campuses"

    if any(word in q for word in facilities_words):
        return "facilities"

    if any(word in q for word in department_words):
        return "faculty and departments"

    return None


def get_allowed_categories(intent):
    if intent == "hostels":
        return ["hostels"]

    if intent == "admission":
        return ["admission", "testing service for admission"]

    if intent == "fees":
        return ["fees", "admission"]

    if intent == "scholarships":
        return ["scholarships"]

    if intent == "contact":
        return ["contact", "admission", "facilities"]

    if intent == "it_director":
        return ["faculty and departments"]

    if intent == "faculty and departments":
        return ["faculty and departments", "admission"]

    if intent == "about university":
        return ["about university"]

    if intent == "campuses":
        return ["campuses", "about university"]

    if intent == "facilities":
        return ["facilities", "hostels", "campuses"]

    return None


def keyword_search(question: str, intent=None, limit: int = 25):
    chunks = load_chunks()

    query = normalize_text(expand_abbreviations(question))
    query_words = set(query.split())

    allowed_categories = get_allowed_categories(intent)

    results = []

    for chunk in chunks:
        content = chunk.get("text", "")
        source = chunk.get("source", "")
        category = chunk.get("category", "")
        chunk_id = chunk.get("chunk_id", "")

        if allowed_categories and category not in allowed_categories:
            continue

        full_text = normalize_text(f"{source} {category} {content}")

        score = 0

        # Basic word overlap
        for word in query_words:
            if len(word) > 2 and word in full_text:
                score += 1

        # -------------------------
        # Intent-specific boosting
        # -------------------------

        if intent == "hostels":
            if category == "hostels":
                score += 50
            if "hostel" in full_text or "hostels" in full_text:
                score += 25
            if "residential and hostel facilities" in full_text:
                score += 30
            if "boarding facility" in full_text:
                score += 20
            if "sixteen hostels" in full_text:
                score += 20
            if "cafeteria" in full_text:
                score += 15
            if "dining hall" in full_text:
                score += 15
            if "common room" in full_text:
                score += 15
            if "indoor games" in full_text:
                score += 15
            if "computer labs" in full_text:
                score += 15
            if "reading room" in full_text:
                score += 15
            if "library" in full_text:
                score += 10
            if "mosque" in full_text:
                score += 10
            if "sports club" in full_text:
                score += 10
            if "gym" in full_text:
                score += 10
            if "laundry" in full_text:
                score += 10
            if "study parks" in full_text:
                score += 15
            if "high speed internet" in full_text:
                score += 15

        elif intent == "it_director":
            if category == "faculty and departments":
                score += 20
            if "director it" in full_text:
                score += 40
            if "serves as director it" in full_text:
                score += 50
            if "faisal shahzad" in full_text:
                score += 40
            if "directorate information technology" in full_text:
                score += 20
            if "dit iub edu pk" in full_text:
                score += 10
            if "phone" in full_text and "email" in full_text:
                score += 10

        elif intent == "admission":
            if category == "admission":
                score += 40
            if "admission" in full_text:
                score += 20
            if "eligibility" in full_text or "criteria" in full_text:
                score += 20
            if "bachelor degree programs" in full_text:
                score += 20
            if "fa fsc" in full_text or "ics" in full_text or "intermediate" in full_text:
                score += 15
            if "iub test" in full_text:
                score += 15
            if "computer science" in query and "computer science" in full_text:
                score += 25
            if "artificial intelligence" in query and "artificial intelligence" in full_text:
                score += 25
            if "software engineering" in query and "software engineering" in full_text:
                score += 25
            if "data science" in query and "data science" in full_text:
                score += 25
            if "information technology" in query and "information technology" in full_text:
                score += 25

        elif intent == "scholarships":
            if category == "scholarships":
                score += 50
            if "scholarship" in full_text or "scholarships" in full_text:
                score += 25
            if "stipend" in full_text:
                score += 10
            if "tuition fee" in full_text:
                score += 10
            if "ehsaas" in full_text:
                score += 15
            if "diya" in full_text:
                score += 15
            if "beef" in full_text:
                score += 15
            if "nest" in full_text:
                score += 15

        elif intent == "fees":
            if category == "fees":
                score += 50
            if "fee" in full_text or "fees" in full_text:
                score += 25
            if "dues" in full_text:
                score += 15
            if "challan" in full_text:
                score += 10
            if "tuition" in full_text:
                score += 10

        elif intent == "contact":
            if category == "contact":
                score += 50
            if "contact" in full_text:
                score += 20
            if "phone" in full_text or "email" in full_text:
                score += 20
            if "helpline" in full_text:
                score += 20
            if "admission iub edu pk" in full_text:
                score += 10
            if "iubhelpline" in full_text:
                score += 10

        elif intent == "about university":
            if category == "about university":
                score += 50
            if "islamia university of bahawalpur" in full_text:
                score += 20
            if "jamia abbasia" in full_text:
                score += 20
            if "established" in full_text:
                score += 10
            if "history" in full_text:
                score += 10
            if "governance" in full_text:
                score += 10

        elif intent == "campuses":
            if category == "campuses":
                score += 50
            if "campus" in full_text or "campuses" in full_text:
                score += 20
            if "baghdad" in full_text:
                score += 10
            if "abbasia" in full_text:
                score += 10
            if "bahawalnagar" in full_text:
                score += 10
            if "rahim yar khan" in full_text:
                score += 10

        elif intent == "facilities":
            if category == "facilities":
                score += 40
            if "facility" in full_text or "facilities" in full_text:
                score += 20
            if "library" in full_text:
                score += 10
            if "transport" in full_text:
                score += 10
            if "sports" in full_text:
                score += 10
            if "medical" in full_text:
                score += 10
            if "hostel" in full_text:
                score += 10

        # Penalize unrelated categories for specific intents
        if intent == "hostels" and category != "hostels":
            score -= 30

        if intent == "admission" and category not in ["admission", "testing service for admission"]:
            score -= 30

        if intent == "scholarships" and category != "scholarships":
            score -= 30

        if intent == "fees" and category != "fees":
            score -= 30

        if score > 0:
            results.append(
                {
                    "content": content,
                    "metadata": {
                        "source": source,
                        "category": category,
                        "file_type": chunk.get("file_type"),
                        "file_path": chunk.get("file_path"),
                        "chunk_id": chunk_id,
                    },
                    # Lower score is better, same style as vector distance
                    "score": 1 / score,
                    "retrieval_type": "keyword",
                }
            )

    results = sorted(results, key=lambda x: x["score"])

    return results[:limit]


def vector_search(question: str, intent=None, k: int = 25):
    vector_db = get_cached_vector_db()

    expanded_question = expand_abbreviations(question)
    allowed_categories = get_allowed_categories(intent)

    all_results = []

    if allowed_categories:
        for category in allowed_categories:
            try:
                results = vector_db.similarity_search_with_score(
                    query=expanded_question,
                    k=k,
                    filter={"category": category},
                )
                all_results.extend(results)
            except Exception:
                continue
    else:
        all_results = vector_db.similarity_search_with_score(
            query=expanded_question,
            k=k,
        )

    documents = []

    for doc, score in all_results:
        documents.append(
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
                "retrieval_type": "vector",
            }
        )

    return documents


def rerank_results(question: str, documents, intent=None, k: int = 5):
    query = normalize_text(expand_abbreviations(question))

    reranked = []
    seen = set()

    for doc in documents:
        source = doc["metadata"].get("source")
        category = doc["metadata"].get("category")
        chunk_id = doc["metadata"].get("chunk_id")

        unique_key = (source, chunk_id)

        if unique_key in seen:
            continue

        seen.add(unique_key)

        content = normalize_text(doc["content"])
        source_text = normalize_text(str(source))

        score = doc["score"]

        # -------------------------
        # Intent-specific reranking
        # -------------------------

        if intent == "hostels":
            if category == "hostels":
                score -= 1.00
            if "residential and hostel facilities" in source_text:
                score -= 0.80
            if "hostel" in content or "hostels" in content:
                score -= 0.50
            if "cafeteria" in content or "dining hall" in content:
                score -= 0.40
            if "common room" in content or "indoor games" in content:
                score -= 0.30
            if "computer labs" in content or "high speed internet" in content:
                score -= 0.30
            if "reading room" in content or "library" in content:
                score -= 0.20
            if "gym" in content or "laundry" in content:
                score -= 0.20

        elif intent == "it_director":
            if category == "faculty and departments":
                score -= 0.30
            if "director it" in content:
                score -= 0.90
            if "serves as director it" in content:
                score -= 1.20
            if "faisal shahzad" in content:
                score -= 0.80
            if "directorate" in source_text and "it" in source_text:
                score -= 0.30

        elif intent == "admission":
            if category == "admission":
                score -= 0.80
            if "admission" in content:
                score -= 0.40
            if "eligibility" in content or "criteria" in content:
                score -= 0.40
            if "bachelor degree programs" in content:
                score -= 0.40
            if "computer science" in query and "computer science" in content:
                score -= 0.60
            if "artificial intelligence" in query and "artificial intelligence" in content:
                score -= 0.60
            if "software engineering" in query and "software engineering" in content:
                score -= 0.60
            if "data science" in query and "data science" in content:
                score -= 0.60
            if "information technology" in query and "information technology" in content:
                score -= 0.60
            if category == "faculty and departments":
                score += 0.80

        elif intent == "scholarships":
            if category == "scholarships":
                score -= 1.00
            if "scholarship" in content:
                score -= 0.40
            if "stipend" in content or "tuition fee" in content:
                score -= 0.20

        elif intent == "fees":
            if category == "fees":
                score -= 1.00
            if "fee" in content or "fees" in content:
                score -= 0.40
            if "dues" in content:
                score -= 0.20

        elif intent == "contact":
            if category == "contact":
                score -= 1.00
            if "phone" in content or "email" in content:
                score -= 0.30
            if "helpline" in content:
                score -= 0.30

        elif intent == "about university":
            if category == "about university":
                score -= 1.00
            if "islamia university of bahawalpur" in content:
                score -= 0.30
            if "jamia abbasia" in content:
                score -= 0.30

        elif intent == "campuses":
            if category == "campuses":
                score -= 1.00
            if "campus" in content or "campuses" in content:
                score -= 0.30

        elif intent == "facilities":
            if category == "facilities":
                score -= 0.80
            if category == "hostels":
                score -= 0.30
            if "facility" in content or "facilities" in content:
                score -= 0.30

        doc["score"] = score
        reranked.append(doc)

    reranked = sorted(reranked, key=lambda x: x["score"])

    return reranked[:k]


def retrieve_relevant_documents(question: str, k: int = 5):
    intent = detect_intent(question)

    bm25_results = bm25_search(question, limit=40)
    keyword_results = keyword_search(question, intent=intent, limit=30)
    vector_results = vector_search(question, intent=intent, k=30)

    combined_results = bm25_results + keyword_results + vector_results

    final_docs = rerank_results(
        question=question,
        documents=combined_results,
        intent=intent,
        k=k,
    )

    return final_docs
