from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_ollama import OllamaLLM

from rag.retrieval import retrieve_relevant_documents
from rag.prompts import SYSTEM_PROMPT
from rag.context_validator import validate_context_for_question
from rag.kb_answer import answer_from_kb


FALLBACK_ANSWER = (
    "Sorry, I could not find official information about this."
)

SPECIFIC_PROGRAM_FALLBACK = (
    "Sorry, I could not find official information about this specific program."
)


app = FastAPI(title="IUB Offline RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


llm = OllamaLLM(
    model="iub-rag-fast",
    temperature=0,
    keep_alive="30m",
)


class ChatRequest(BaseModel):
    question: str
    last_question: str = ""


def build_context(retrieved_docs):
    context_parts = []

    for index, doc in enumerate(retrieved_docs, start=1):
        category = doc["metadata"].get("category", "unknown")
        content = doc.get("content", "")

        context_parts.append(
            f"Document {index}\n"
            f"Category: {category}\n"
            f"Content:\n{content}"
        )

    return "\n\n---\n\n".join(context_parts)


def build_sources(retrieved_docs):
    sources = []

    for doc in retrieved_docs:
        source_info = {
            "source": doc["metadata"].get("source"),
            "category": doc["metadata"].get("category"),
            "score": doc.get("score"),
        }

        if source_info not in sources:
            sources.append(source_info)

    return sources


def clean_answer(answer):
    if not answer:
        return FALLBACK_ANSWER

    answer = str(answer).strip()

    if not answer:
        return FALLBACK_ANSWER

    return answer


@app.get("/")
def home():
    return {
        "message": "IUB Offline RAG Chatbot Backend is running."
    }


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        return {
            "answer": "Please enter a valid question.",
            "sources": [],
        }

    kb_result = answer_from_kb(question, request.last_question)
    if kb_result is not None:
        return kb_result

    retrieved_docs = retrieve_relevant_documents(question, k=5)

    if not retrieved_docs:
        return {
            "answer": FALLBACK_ANSWER,
            "sources": [],
        }

    sources = build_sources(retrieved_docs)

    if not validate_context_for_question(question, retrieved_docs):
        return {
            "answer": SPECIFIC_PROGRAM_FALLBACK,
            "sources": sources,
        }

    context = build_context(retrieved_docs)

    prompt = SYSTEM_PROMPT.format(
        context=context,
        question=question,
    )

    answer = llm.invoke(prompt)
    answer = clean_answer(answer)

    return {
        "answer": answer,
        "sources": sources,
    }
