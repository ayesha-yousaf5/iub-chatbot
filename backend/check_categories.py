from rag.vector_store import load_vector_store

db = load_vector_store()
results = db._collection.get(limit=500)

print("All categories in vector store:")

categories = set()
for metadata in results['metadatas']:
    cat = metadata.get('category', 'unknown')
    if cat not in categories:
        categories.add(cat)
        print(f"  - {cat}")

print(f"\nTotal unique categories: {len(categories)}")

# Now check specifically for about/history/governance documents
print("\n\nSearch for 'history' related docs:")
for i, metadata in enumerate(results['metadatas']):
    if 'history' in metadata.get('source', '').lower() or 'governance' in metadata.get('source', '').lower() or 'vision' in metadata.get('source', '').lower():
        print(f"  Source: {metadata.get('source')}, Category: {metadata.get('category')}")
