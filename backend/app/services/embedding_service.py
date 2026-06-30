import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.db.models import EMBEDDING_DIMENSION


load_dotenv()


GEMINI_EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "gemini-embedding-2",
)

GEMINI_EMBEDDING_DIMENSION = int(
    os.getenv(
        "GEMINI_EMBEDDING_DIMENSION",
        str(EMBEDDING_DIMENSION),
    )
)


def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY. Please add it to backend/.env."
        )

    return genai.Client(api_key=api_key)


def prepare_document_text(title: str, content: str) -> str:
    return f"title: {title} | text: {content}"


def prepare_query_text(query: str) -> str:
    return f"task: question answering | query: {query}"


def generate_embedding(text: str) -> list[float]:
    client = get_gemini_client()

    result = client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=GEMINI_EMBEDDING_DIMENSION,
        ),
    )

    if not result.embeddings:
        raise RuntimeError("Gemini embedding response did not contain embeddings.")

    embedding = result.embeddings[0].values

    if len(embedding) != EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Expected embedding dimension {EMBEDDING_DIMENSION}, "
            f"but got {len(embedding)}."
        )

    return list(embedding)


def generate_document_embedding(title: str, content: str) -> list[float]:
    document_text = prepare_document_text(
        title=title,
        content=content,
    )

    return generate_embedding(document_text)


def generate_query_embedding(query: str) -> list[float]:
    query_text = prepare_query_text(query)

    return generate_embedding(query_text)