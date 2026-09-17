from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-en-v1.5"
SAVE_PATH = "local_models/bge-small-en-v1.5"


def main():
    print("Downloading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    model.save(SAVE_PATH)
    print(f"Embedding model saved at: {SAVE_PATH}")


if __name__ == "__main__":
    main()