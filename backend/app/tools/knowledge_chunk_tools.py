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


def calculate_chunk_score(chunk: KnowledgeChunk, search_terms: list[str]) -> int:
    score = 0

    document_id = chunk.document_id.lower()
    title = chunk.title.lower()
    content = chunk.content.lower()
    source = chunk.source.lower()

    for term in search_terms:
        if term in document_id:
            score += 6

        if term in title:
            score += 5

        if term in source:
            score += 4

        if term in content:
            score += 3

    return score


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
        filters.append(KnowledgeChunk.document_id.ilike(pattern))
        filters.append(KnowledgeChunk.title.ilike(pattern))
        filters.append(KnowledgeChunk.content.ilike(pattern))
        filters.append(KnowledgeChunk.source.ilike(pattern))

    chunks = (
        db.query(KnowledgeChunk)
        .filter(or_(*filters))
        .all()
    )

    ranked_chunks = sorted(
        chunks,
        key=lambda chunk: calculate_chunk_score(chunk, search_terms),
        reverse=True,
    )

    return [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "title": chunk.title,
            "content": chunk.content,
            "source": chunk.source,
        }
        for chunk in ranked_chunks[:limit]
    ]