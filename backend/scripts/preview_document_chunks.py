from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from app.services.document_chunking import load_and_chunk_support_documents


DOCUMENTS_DIR = (
    BACKEND_DIR
    / "app"
    / "data"
    / "support_documents"
)


def main() -> None:
    chunks = load_and_chunk_support_documents(
        documents_dir=DOCUMENTS_DIR,
        max_chars=300,
    )

    print(f"Loaded {len(chunks)} chunks\n")

    for chunk in chunks:
        print("=" * 80)
        print(f"Document ID: {chunk['document_id']}")
        print(f"Title: {chunk['title']}")
        print(f"Source: {chunk['source']}")
        print(f"Chunk Index: {chunk['chunk_index']}")
        print("-" * 80)
        print(chunk["content"])
        print()


if __name__ == "__main__":
    main()