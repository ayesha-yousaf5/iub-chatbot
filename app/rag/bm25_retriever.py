import os
import json
import re

from rank_bm25 import BM25Okapi

from rag.query_processor import expand_abbreviations


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNKS_PATH = os.path.join(BASE_DIR, "processed_data", "chunks.json")


BM25_INDEX = None
BM25_CHUNKS = None
BM25_TOKENIZED_CORPUS = None


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    replacements = {
        "deprtment": "department",
        "camouses": "campuses",
        "camouse": "campus",
        "feeof": "fee of",
        "doit": "directorate of information technology",
        "deptt": "department",
        "dept": "department",
        "b.s.": "bs",
        "m.phil": "mphil",
        "ph.d": "phd",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9\s&\-\/\.]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def tokenize(text: str):
    text = normalize_text(text)

    tokens = []

    for token in text.split():
        token = token.strip()

        if not token:
            continue

        # Keep useful short tokens like BS, IT, AI, CS
        if len(token) <= 2 and token not in ["bs", "it", "ai", "cs", "ms"]:
            continue

        tokens.append(token)

    return tokens


def load_chunks():
    if not os.path.exists(CHUNKS_PATH):
        raise FileNotFoundError(
            f"chunks.json not found at {CHUNKS_PATH}. "
            "Run this first: python -m rag.ingest"
        )

    with open(CHUNKS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def build_bm25_index():
    global BM25_INDEX, BM25_CHUNKS, BM25_TOKENIZED_CORPUS

    if BM25_INDEX is not None:
        return BM25_INDEX, BM25_CHUNKS

    chunks = load_chunks()

    corpus = []

    for chunk in chunks:
        combined_text = (
            f"{chunk.get('source', '')} "
            f"{chunk.get('category', '')} "
            f"{chunk.get('text', '')}"
        )

        corpus.append(tokenize(combined_text))

    BM25_CHUNKS = chunks
    BM25_TOKENIZED_CORPUS = corpus
    BM25_INDEX = BM25Okapi(corpus)

    return BM25_INDEX, BM25_CHUNKS


def calculate_exact_boost(question: str, chunk):
    q = normalize_text(question)

    content = normalize_text(chunk.get("text", ""))
    source = normalize_text(chunk.get("source", ""))
    category = normalize_text(chunk.get("category", ""))

    full_text = f"{source} {category} {content}"

    boost = 0.0

    # Strong boost if full important phrase appears
    important_phrases = extract_important_phrases(q)

    for phrase in important_phrases:
        if phrase and phrase in full_text:
            boost += 8.0

    # Source name match is very valuable
    for phrase in important_phrases:
        if phrase and phrase in source:
            boost += 12.0

    # Contact-type boost
    if any(word in q for word in ["contact", "phone", "email", "number"]):
        if any(word in full_text for word in ["phone", "email", "@", "contact"]):
            boost += 4.0

    # Fee-policy boost
    if any(word in q for word in ["hostel dues", "transport charges", "included", "not included"]):
        if any(word in full_text for word in ["not included", "charged separately", "hostel dues", "transport charges"]):
            boost += 10.0

    # Facilities boost
    if "facility" in q or "facilities" in q:
        if category == "facilities":
            boost += 8.0

    # Faculty/departments boost
    if any(word in q for word in ["faculty", "department", "directorate", "division", "center", "centre", "office", "institute"]):
        if category == "faculty and departments":
            boost += 8.0

    return boost


def extract_important_phrases(query: str):
    phrases = []

    # Whole query phrase after removing common question words
    cleaned = query

    common_words = [
        "what is", "who is", "tell me about", "explain about",
        "what are", "how can i", "how many", "at iub", "of iub",
        "the", "a", "an", "please"
    ]

    for word in common_words:
        cleaned = cleaned.replace(word, " ")

    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned) >= 4:
        phrases.append(cleaned)

    # Entity-style phrases
    patterns = [
        r"faculty of [a-z0-9 &\-\/]+",
        r"department of [a-z0-9 &\-\/]+",
        r"directorate of [a-z0-9 &\-\/]+",
        r"division of [a-z0-9 &\-\/]+",
        r"center for [a-z0-9 &\-\/]+",
        r"centre for [a-z0-9 &\-\/]+",
        r"institute of [a-z0-9 &\-\/]+",
        r"office of [a-z0-9 &\-\/]+",
        r"bs [a-z0-9 &\-\/]+",
        r"mphil [a-z0-9 &\-\/]+",
        r"phd [a-z0-9 &\-\/]+",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, query)

        for match in matches:
            match = match.strip()
            if match:
                phrases.append(match)

    # Remove duplicates
    unique = []
    seen = set()

    for phrase in phrases:
        if phrase not in seen:
            seen.add(phrase)
            unique.append(phrase)

    return unique


def bm25_search(question: str, limit: int = 30):
    bm25, chunks = build_bm25_index()

    expanded_question = expand_abbreviations(question)
    query_tokens = tokenize(expanded_question)

    scores = bm25.get_scores(query_tokens)

    results = []

    for index, score in enumerate(scores):
        chunk = chunks[index]

        exact_boost = calculate_exact_boost(question, chunk)
        final_score = float(score) + exact_boost

        if final_score <= 0:
            continue

        results.append(
            {
                "content": chunk.get("text", ""),
                "metadata": {
                    "source": chunk.get("source", ""),
                    "category": chunk.get("category", ""),
                    "file_type": chunk.get("file_type", ""),
                    "file_path": chunk.get("file_path", ""),
                    "chunk_id": chunk.get("chunk_id", ""),
                },
                # Negative because current reranker sorts lower score first
                "score": -final_score,
                "retrieval_type": "bm25",
            }
        )

    results = sorted(results, key=lambda x: x["score"])

    return results[:limit]