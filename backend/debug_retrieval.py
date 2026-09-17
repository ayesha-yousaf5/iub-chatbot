from rag.retrieval import retrieve_relevant_documents, detect_intent, get_allowed_categories

question = "tell about iub"

intent = detect_intent(question)
categories = get_allowed_categories(intent)

print(f"Question: {question}")
print(f"Intent: {intent}")
print(f"Allowed Categories: {categories}")
print("="*60)

docs = retrieve_relevant_documents(question, k=5)
print(f"\nDocuments retrieved: {len(docs)}")
for i, doc in enumerate(docs, 1):
    src = doc['metadata'].get('source', 'unknown')
    cat = doc['metadata'].get('category', 'unknown')
    score = doc.get('score', 'N/A')
    print(f"{i}. Source: {src} | Category: {cat} | Score: {score}")