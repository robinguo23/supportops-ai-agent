from pathlib import Path
import sys

from sqlalchemy.orm import Session


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from app.db.init_db import init_db
from app.db.models import KnowledgeChunk
from app.db.session import SessionLocal
from app.services.document_chunking import load_and_chunk_support_documents
from app.services.embedding_service import generate_document_embedding


DOCUMENTS_DIR = (
    BACKEND_DIR
    / "app"
    / "data"
    / "support_documents"
)


def clear_existing_chunks(db: Session) -> None:
    db.query(KnowledgeChunk).delete()
    db.commit()


def insert_chunks(db: Session) -> int:
    chunks = load_and_chunk_support_documents(
        documents_dir=DOCUMENTS_DIR,
        max_chars=300,
    )

    for index, chunk in enumerate(chunks, start=1):
        print(
            f"Generating embedding for chunk {index}/{len(chunks)}: "
            f"{chunk['source']} #{chunk['chunk_index']}"
        )

        embedding = generate_document_embedding(
            title=chunk["title"],
            content=chunk["content"],
        )

        knowledge_chunk = KnowledgeChunk(
            document_id=chunk["document_id"],
            title=chunk["title"],
            content=chunk["content"],
            source=chunk["source"],
            embedding=embedding,
        )

        db.add(knowledge_chunk)

    db.commit()

    return len(chunks)


def main() -> None:
    init_db()

    db = SessionLocal()

    try:
        clear_existing_chunks(db)
        inserted_count = insert_chunks(db)

        print(
            f"Inserted {inserted_count} knowledge chunks "
            "with real Gemini embeddings into the database."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()