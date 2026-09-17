from rag.answer_guard import _important_terms
from rag.retrieval import retrieve_relevant_documents

question = "tell about iub"

terms = _important_terms(question)
print(f"Question: {question}")
print(f"Important terms: {terms}")

docs = retrieve_relevant_documents(question, k=5)
print(f"\nDocuments retrieved: {len(docs)}")

# Check if terms exist in documents
for i, doc in enumerate(docs, 1):
    content = doc.get("content", "").lower()
    matching_terms = [t for t in terms if t in content]
    print(f"{i}. Matches: {matching_terms}")
