from rag.vector_store import load_vector_store

db = load_vector_store()
results = db._collection.get(limit=100)

print(f"Total items in vector store: {db._collection.count()}\n")
print("Document sources found:")

sources = set()
for metadata in results['metadatas']:
    source = metadata.get('source', 'unknown')
    if source not in sources:
        sources.add(source)
        print(f"  - {source}")

print(f"\nTotal unique sources: {len(sources)}")
