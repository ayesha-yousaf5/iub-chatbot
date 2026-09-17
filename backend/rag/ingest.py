import os
import json

from rag.extract import extract_all_data
from rag.clean import clean_text
from rag.chunk import chunk_documents
from rag.vector_store import create_vector_store


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)

DATA_RAW_DIR = os.path.join(PROJECT_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")


def save_json(data, file_name):
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    file_path = os.path.join(PROCESSED_DIR, file_name)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"Saved: {file_path}")


def main():
    print("Starting IUB offline RAG ingestion...")
    print(f"Reading documents from: {DATA_RAW_DIR}")

    if not os.path.exists(DATA_RAW_DIR):
        print("data/raw folder not found. Please check your project structure.")
        return

    documents = extract_all_data(DATA_RAW_DIR)

    print(f"Documents extracted: {len(documents)}")

    if not documents:
        print("No documents found. Please check your data/raw folder.")
        return

    cleaned_documents = []

    for doc in documents:
        cleaned_documents.append(
            {
                **doc,
                "text": clean_text(doc["text"]),
            }
        )

    save_json(cleaned_documents, "cleaned_documents.json")

    chunks = chunk_documents(cleaned_documents)

    print(f"Chunks created: {len(chunks)}")

    if not chunks:
        print("No chunks created. Please check chunk.py or extracted document text.")
        return

    save_json(chunks, "chunks.json")

    create_vector_store(chunks, reset_db=True)

    print("Ingestion completed successfully.")


if __name__ == "__main__":
    main()