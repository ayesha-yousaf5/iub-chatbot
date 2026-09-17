import os
import shutil

# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_core.documents import Document

from rag.embeddings import load_embedding_model


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")


def create_vector_store(chunks, reset_db: bool = True):
    if reset_db and os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)

    embedding_model = load_embedding_model()

    documents = []

    for chunk in chunks:
        document = Document(
            page_content=chunk["text"],
            metadata={
                "source": chunk["source"],
                "category": chunk["category"],
                "file_type": chunk["file_type"],
                "file_path": chunk["file_path"],
                "chunk_id": chunk["chunk_id"],
            },
        )

        documents.append(document)

    vector_db = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=CHROMA_DIR,
        collection_name="iub_university_data",
    )

    print(f"Vector database created successfully at: {CHROMA_DIR}")
    print(f"Total chunks stored: {len(documents)}")

    return vector_db


def load_vector_store():
    embedding_model = load_embedding_model()

    vector_db = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embedding_model,
        collection_name="iub_university_data",
    )

    return vector_db