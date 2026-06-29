from app.data.knowledge_base import KNOWLEDGE_BASE


def search_knowledge_base(message: str) -> dict | None:
    normalized_message = message.lower()

    for article in KNOWLEDGE_BASE:
        for keyword in article["keywords"]:
            if keyword in normalized_message:
                return {
                    "article_id": article["id"],
                    "title": article["title"],
                    "answer": article["answer"],
                }

    return None