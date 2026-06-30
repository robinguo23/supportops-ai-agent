import os

from openai import OpenAI


DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_CHAT_MODEL = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-v4-flash")


def format_retrieved_context(retrieved_chunks: list[dict]) -> str:
    context_blocks = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        title = chunk.get("title", "Untitled Policy")
        source = chunk.get("source", "unknown source")
        content = chunk.get("content", "")

        context_blocks.append(
            f"[Source {index}]\n"
            f"Title: {title}\n"
            f"Source file: {source}\n"
            f"Content:\n{content}"
        )

    return "\n\n---\n\n".join(context_blocks)


def generate_support_answer(
    *,
    user_question: str,
    retrieved_chunks: list[dict],
) -> str:
    """
    Generate a customer-friendly answer using only retrieved support policy chunks.

    Important:
    - Retrieval is still done before this function.
    - The LLM must not invent company policy.
    - Sources are still handled by the retrieval layer and frontend.
    """

    if not retrieved_chunks:
        return (
            "I could not find enough information in the support policy documents "
            "to answer this confidently. You may request human support."
        )

    if not DEEPSEEK_API_KEY:
        top_chunk = retrieved_chunks[0]
        title = top_chunk.get("title", "Support Policy")
        content = top_chunk.get("content", "")

        return (
            f"Based on our support policy: {title}\n\n"
            f"{content}\n\n"
            "Did this solve your issue?"
        )

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )

    retrieved_context = format_retrieved_context(retrieved_chunks)

    system_prompt = """
You are a customer support assistant.

You must answer ONLY using the retrieved support policy context provided by the system.

Rules:
- Do not invent company policies.
- Do not use outside knowledge.
- Do not mention policies that are not in the provided context.
- If the context is insufficient, say that you cannot confirm this from the available policy documents.
- Keep the answer concise, polite, and practical.
- If useful, tell the customer what information they should provide, such as an order ID, photo, payment date, or issue description.
- Do not include fake source names.
- Do not say "according to Source 1" in the final answer.
""".strip()

    user_prompt = f"""
Customer question:
{user_question}

Retrieved support policy context:
{retrieved_context}

Write a helpful customer support answer based only on the retrieved context.
""".strip()

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.2,
            max_tokens=350,
        )

        answer = response.choices[0].message.content

        if not answer:
            raise ValueError("DeepSeek returned an empty answer.")

        return answer.strip()

    except Exception as error:
        print(f"DeepSeek answer generation failed: {error}")

        top_chunk = retrieved_chunks[0]
        title = top_chunk.get("title", "Support Policy")
        content = top_chunk.get("content", "")

        return (
            f"Based on our support policy: {title}\n\n"
            f"{content}\n\n"
            "Did this solve your issue?"
        )