from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from app.services.embedding_service import generate_query_embedding


def main() -> None:
    query = "How long does a refund take?"

    embedding = generate_query_embedding(query)

    print(f"Query: {query}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")


if __name__ == "__main__":
    main()