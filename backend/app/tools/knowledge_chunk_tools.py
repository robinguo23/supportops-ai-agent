import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import KnowledgeChunk


STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "do",
    "does",
    "can",
    "i",
    "you",
    "your",
    "my",
    "to",
    "of",
    "and",
    "or",
    "in",
    "on",
    "for",
    "with",
    "what",
    "how",
    "when",
    "where",
}


def extract_search_terms(query: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+", query.lower())

    return [
        word
        for word in words
        if len(word) > 2 and word not in STOPWORDS
    ]


def search_knowledge_chunks(
    db: Session,
    query: str,
    limit: int = 3,
) -> list[dict]:
    search_terms = extract_search_terms(query)

    if not search_terms:
        return []

    filters = []

    for term in search_terms:
        pattern = f"%{term}%"
        filters.append(KnowledgeChunk.title.ilike(pattern))
        filters.append(KnowledgeChunk.content.ilike(pattern))
        filters.append(KnowledgeChunk.source.ilike(pattern))

    chunks = (
        db.query(KnowledgeChunk)
        .filter(or_(*filters))
        .order_by(KnowledgeChunk.id)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "title": chunk.title,
            "content": chunk.content,
            "source": chunk.source,
        }
        for chunk in chunks
    ]