from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=120,
        separators=["\n\n", "\n", ".", "?", "!", " ", ""],
    )

    chunks = []

    for doc in documents:
        text_chunks = splitter.split_text(doc["text"])

        for index, chunk in enumerate(text_chunks):
            chunks.append(
                {
                    "text": chunk,
                    "source": doc["source"],
                    "category": doc["category"],
                    "file_type": doc["file_type"],
                    "file_path": doc["file_path"],
                    "chunk_id": index,
                }
            )

    return chunks