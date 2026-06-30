from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.chat import ChatRequest, ChatResponse
from app.services.embedding_service import generate_query_embedding
from app.services.knowledge_base import search_knowledge_base
from app.tools.knowledge_chunk_tools import (
    search_knowledge_chunks,
    search_knowledge_chunks_by_embedding,
)
from app.tools.order_tools import check_order_status, extract_order_id
from app.tools.ticket_tools import (
    create_support_ticket,
    list_support_tickets,
    update_support_ticket_status,
)


router = APIRouter()


MIN_RAG_SIMILARITY = 0.60


SUPPORT_DOMAIN_TERMS = (
    "order",
    "orders",
    "return",
    "returns",
    "refund",
    "refunds",
    "delivery",
    "shipping",
    "parcel",
    "item",
    "items",
    "damaged",
    "faulty",
    "broken",
    "cancel",
    "payment",
    "charged",
    "address",
)


class EscalationRequest(BaseModel):
    original_question: str
    reason: str | None = None


def clean_chunk_content(content: str) -> str:
    cleaned_lines = []

    for line in content.splitlines():
        stripped_line = line.strip()

        if stripped_line.startswith("#"):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def build_policy_reply(top_chunk: dict) -> str:
    cleaned_content = clean_chunk_content(top_chunk["content"])

    return (
        f"Based on our support policy: {top_chunk['title']}\n\n"
        f"{cleaned_content}"
    )


def is_support_domain_query(message: str) -> bool:
    normalized_message = message.lower()

    return any(
        term in normalized_message
        for term in SUPPORT_DOMAIN_TERMS
    )


def build_sources(knowledge_chunks: list[dict]) -> list[dict]:
    return [
        {
            "document_id": chunk["document_id"],
            "title": chunk["title"],
            "source": chunk["source"],
            "similarity": chunk.get("similarity"),
        }
        for chunk in knowledge_chunks
    ]


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    order_id = extract_order_id(request.message)

    if order_id:
        tool_result = check_order_status(order_id)

        if tool_result["found"]:
            return ChatResponse(
                reply=(
                    f"I found your order {order_id}. "
                    f"The current status is {tool_result['status']}. "
                    f"The estimated delivery date is {tool_result['estimated_delivery']} "
                    f"via {tool_result['carrier']}."
                ),
                needs_human_handoff=False,
                tool_used="check_order_status",
                tool_result={
                    **tool_result,
                    "conversation_action": "ask_resolution_feedback",
                    "original_query": request.message,
                },
            )

        return ChatResponse(
            reply=(
                f"I could not find order {order_id}. "
                "Would you like to request human support for this issue?"
            ),
            needs_human_handoff=False,
            tool_used="order_not_found",
            tool_result={
                "reason": "order_not_found",
                "order_id": order_id,
                "conversation_action": "ask_escalation",
                "original_query": request.message,
            },
        )

    if not is_support_domain_query(request.message):
        return ChatResponse(
            reply=(
                "I can only help with support questions about orders, returns, "
                "refunds, delivery, or damaged items."
            ),
            needs_human_handoff=False,
            tool_used="out_of_scope_guardrail",
            tool_result={
                "reason": "out_of_scope",
                "conversation_action": "allow_new_question",
                "original_query": request.message,
            },
        )

    query_embedding = generate_query_embedding(request.message)

    knowledge_chunks = search_knowledge_chunks_by_embedding(
        db=db,
        query_embedding=query_embedding,
        limit=3,
    )

    if knowledge_chunks:
        top_chunk = knowledge_chunks[0]
        top_similarity = top_chunk.get("similarity", 0)
        sources = build_sources(knowledge_chunks)

        if top_similarity >= MIN_RAG_SIMILARITY:
            return ChatResponse(
                reply=build_policy_reply(top_chunk),
                needs_human_handoff=False,
                tool_used="knowledge_vector_search",
                tool_result={
                    "matched_chunks": knowledge_chunks,
                    "sources": sources,
                    "min_similarity": MIN_RAG_SIMILARITY,
                    "conversation_action": "ask_resolution_feedback",
                    "original_query": request.message,
                },
            )

        return ChatResponse(
            reply=(
                "I could not find a strong enough support policy match for this question. "
                "Would you like to request human support?"
            ),
            needs_human_handoff=False,
            tool_used="knowledge_vector_search",
            tool_result={
                "matched_chunks": knowledge_chunks,
                "min_similarity": MIN_RAG_SIMILARITY,
                "reason": "top_similarity_below_threshold",
                "conversation_action": "ask_escalation",
                "original_query": request.message,
            },
        )

    knowledge_result = search_knowledge_base(request.message)

    if knowledge_result:
        return ChatResponse(
            reply=knowledge_result["answer"],
            needs_human_handoff=False,
            tool_used="knowledge_base_search",
            tool_result={
                **knowledge_result,
                "conversation_action": "ask_resolution_feedback",
                "original_query": request.message,
            },
        )

    return ChatResponse(
        reply=(
            "I could not find a relevant support policy for this question. "
            "Would you like to request human support?"
        ),
        needs_human_handoff=False,
        tool_used="knowledge_search_no_match",
        tool_result={
            "reason": "no_relevant_policy_found",
            "conversation_action": "ask_escalation",
            "original_query": request.message,
        },
    )


@router.post("/tickets/escalate")
def escalate_to_human(
    request: EscalationRequest,
    db: Session = Depends(get_db),
):
    ticket = create_support_ticket(
        db=db,
        issue_type="human_escalation",
        summary=(
            f"Customer requested human support. "
            f"Original question: {request.original_question}"
        ),
    )

    return {
        "message": (
            f"I have created support ticket {ticket['ticket_id']} "
            "for a human support agent."
        ),
        "ticket": ticket,
        "reason": request.reason,
    }


@router.get("/tickets")
def get_tickets(limit: int = 20, db: Session = Depends(get_db)):
    tickets = list_support_tickets(db=db, limit=limit)

    return {
        "tickets": tickets,
    }


@router.patch("/tickets/{ticket_id}/status")
def update_ticket_status(
    ticket_id: str,
    status: str,
    db: Session = Depends(get_db),
):
    updated_ticket = update_support_ticket_status(
        db=db,
        ticket_id=ticket_id,
        status=status,
    )

    if updated_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "ticket": updated_ticket,
    }


@router.get("/knowledge/search")
def search_knowledge(
    query: str,
    limit: int = 3,
    db: Session = Depends(get_db),
):
    chunks = search_knowledge_chunks(
        db=db,
        query=query,
        limit=limit,
    )

    return {
        "query": query,
        "count": len(chunks),
        "chunks": chunks,
    }


@router.get("/knowledge/vector-search")
def vector_search_knowledge(
    query: str,
    limit: int = 3,
    db: Session = Depends(get_db),
):
    query_embedding = generate_query_embedding(query)

    chunks = search_knowledge_chunks_by_embedding(
        db=db,
        query_embedding=query_embedding,
        limit=limit,
    )

    return {
        "query": query,
        "count": len(chunks),
        "chunks": chunks,
    }