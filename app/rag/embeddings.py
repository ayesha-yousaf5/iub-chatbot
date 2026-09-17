import os

from langchain_huggingface import HuggingFaceEmbeddings


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCAL_EMBEDDING_MODEL_PATH = os.path.join(
    BASE_DIR,
    "local_models",
    "bge-small-en-v1.5"
)


def load_embedding_model():
    if not os.path.exists(LOCAL_EMBEDDING_MODEL_PATH):
        raise FileNotFoundError(
            f"Local embedding model not found at: {LOCAL_EMBEDDING_MODEL_PATH}. "
            "Run download_embedding_model.py first."
        )

    return HuggingFaceEmbeddings(
        model_name=LOCAL_EMBEDDING_MODEL_PATH,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )