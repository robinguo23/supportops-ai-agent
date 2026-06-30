import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models import SupportTicket
from app.db.session import get_db
from app.models.chat import ChatRequest, ChatResponse
from app.services.answer_generation_service import generate_support_answer
from app.services.embedding_service import generate_query_embedding
from app.tools.knowledge_chunk_tools import (
    search_knowledge_chunks,
    search_knowledge_chunks_by_embedding,
)
from app.tools.order_tools import check_order_status
from app.tools.ticket_tools import create_support_ticket


router = APIRouter()


MIN_RAG_SIMILARITY = 0.60

ORDER_ID_PATTERN = re.compile(r"\bORD-\d+\b", re.IGNORECASE)

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
    "product",
    "products",
    "shoe",
    "shoes",
    "damaged",
    "faulty",
    "broken",
    "defective",
    "cancel",
    "cancellation",
    "payment",
    "billing",
    "charged",
    "charge",
    "address",
    "replacement",
    "exchange",
)


class EscalationRequest(BaseModel):
    original_question: str
    reason: str | None = None


def extract_order_id(message: str) -> str | None:
    match = ORDER_ID_PATTERN.search(message)

    if not match:
        return None

    return match.group(0).upper()


def clean_chunk_content(content: str) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]

    if lines and lines[0].startswith("#"):
        lines = lines[1:]

    return "\n".join(lines).strip()


def build_policy_reply(top_chunk: dict[str, Any]) -> str:
    title = top_chunk.get("title", "Support Policy")
    content = clean_chunk_content(top_chunk.get("content", ""))

    return f"Based on our support policy: {title}\n\n{content}"


def is_support_domain_query(message: str) -> bool:
    lowered_message = message.lower()

    return any(term in lowered_message for term in SUPPORT_DOMAIN_TERMS)


def build_sources(knowledge_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources = []

    for chunk in knowledge_chunks:
        source = {
            "document_id": chunk.get("document_id"),
            "title": chunk.get("title"),
            "source": chunk.get("source"),
        }

        if "similarity" in chunk:
            source["similarity"] = chunk["similarity"]

        sources.append(source)

    return sources


def ticket_to_dict(ticket: SupportTicket | dict[str, Any]) -> dict[str, Any]:
    if isinstance(ticket, dict):
        return ticket

    return {
        "id": ticket.id,
        "ticket_id": ticket.ticket_id,
        "issue_type": ticket.issue_type,
        "summary": ticket.summary,
        "status": ticket.status,
        "created_at": (
            ticket.created_at.isoformat()
            if ticket.created_at is not None
            else None
        ),
    }


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    user_message = request.message.strip()

    if not user_message:
        return ChatResponse(
            reply="Please enter a support question.",
            needs_human_handoff=False,
            tool_used="empty_message_guardrail",
            tool_result={
                "reason": "empty_message",
                "conversation_action": "allow_new_question",
                "original_query": request.message,
            },
        )

    order_id = extract_order_id(user_message)

    if order_id:
        order_result = check_order_status(order_id)

        if order_result and order_result.get("found", True):
            tool_result = {
                **order_result,
                "found": True,
                "order_id": order_id,
                "conversation_action": "ask_resolution_feedback",
                "original_query": user_message,
            }

            return ChatResponse(
                reply=(
                    f"I found your order {order_id}. "
                    f"The current status is: {order_result.get('status', 'unknown')}."
                ),
                needs_human_handoff=False,
                tool_used="check_order_status",
                tool_result=tool_result,
            )

        return ChatResponse(
            reply=(
                f"I could not find order {order_id}. "
                "Would you like to request human support?"
            ),
            needs_human_handoff=False,
            tool_used="order_not_found",
            tool_result={
                "found": False,
                "order_id": order_id,
                "reason": "order_not_found",
                "conversation_action": "ask_escalation",
                "original_query": user_message,
            },
        )

    if not is_support_domain_query(user_message):
        return ChatResponse(
            reply=(
                "I can only help with support questions about orders, returns, "
                "refunds, delivery, damaged items, or billing issues."
            ),
            needs_human_handoff=False,
            tool_used="out_of_scope_guardrail",
            tool_result={
                "reason": "out_of_scope",
                "conversation_action": "allow_new_question",
                "original_query": user_message,
            },
        )

    try:
        query_embedding = generate_query_embedding(user_message)

        knowledge_chunks = search_knowledge_chunks_by_embedding(
            db=db,
            query_embedding=query_embedding,
            limit=3,
        )

        if knowledge_chunks:
            top_chunk = knowledge_chunks[0]
            top_similarity = float(top_chunk.get("similarity", 0.0))

            if top_similarity >= MIN_RAG_SIMILARITY:
                generated_reply = generate_support_answer(
                    user_question=user_message,
                    retrieved_chunks=knowledge_chunks,
                )

                return ChatResponse(
                    reply=generated_reply,
                    needs_human_handoff=False,
                    tool_used="knowledge_vector_search",
                    tool_result={
                        "matched_chunks": knowledge_chunks,
                        "sources": build_sources(knowledge_chunks),
                        "top_similarity": top_similarity,
                        "min_similarity": MIN_RAG_SIMILARITY,
                        "conversation_action": "ask_resolution_feedback",
                        "original_query": user_message,
                    },
                )

            return ChatResponse(
                reply=(
                    "I found some related support information, but it may not "
                    "be confident enough to answer your issue. Would you like "
                    "to request human support?"
                ),
                needs_human_handoff=False,
                tool_used="knowledge_vector_search",
                tool_result={
                    "matched_chunks": knowledge_chunks,
                    "sources": build_sources(knowledge_chunks),
                    "top_similarity": top_similarity,
                    "min_similarity": MIN_RAG_SIMILARITY,
                    "reason": "top_similarity_below_threshold",
                    "conversation_action": "ask_escalation",
                    "original_query": user_message,
                },
            )

    except Exception as error:
        print(f"Vector RAG retrieval failed: {error}")

    keyword_chunks = search_knowledge_chunks(
        db=db,
        query=user_message,
        limit=3,
    )

    if keyword_chunks:
        generated_reply = generate_support_answer(
            user_question=user_message,
            retrieved_chunks=keyword_chunks,
        )

        return ChatResponse(
            reply=generated_reply,
            needs_human_handoff=False,
            tool_used="knowledge_base_search",
            tool_result={
                "matched_chunks": keyword_chunks,
                "sources": build_sources(keyword_chunks),
                "conversation_action": "ask_resolution_feedback",
                "original_query": user_message,
            },
        )

    return ChatResponse(
        reply=(
            "I could not find a confident answer in the support policy "
            "documents. Would you like to request human support?"
        ),
        needs_human_handoff=False,
        tool_used="knowledge_base_search",
        tool_result={
            "matched_chunks": [],
            "sources": [],
            "reason": "no_matching_policy_found",
            "conversation_action": "ask_escalation",
            "original_query": user_message,
        },
    )


@router.post("/tickets/escalate")
def escalate_to_human(
    request: EscalationRequest,
    db: Session = Depends(get_db),
):
    original_question = request.original_question.strip()

    if not original_question:
        raise HTTPException(
            status_code=400,
            detail="original_question is required.",
        )

    ticket = create_support_ticket(
        db=db,
        issue_type="human_escalation",
        summary=(
            "Customer requested human support. "
            f"Original question: {original_question}"
        ),
    )

    return {
        "message": "A human support ticket has been created.",
        "ticket": ticket_to_dict(ticket),
        "reason": request.reason,
    }


@router.get("/tickets")
def list_tickets(db: Session = Depends(get_db)):
    tickets = (
        db.query(SupportTicket)
        .order_by(SupportTicket.created_at.desc())
        .all()
    )

    return {
        "tickets": [ticket_to_dict(ticket) for ticket in tickets],
    }


@router.patch("/tickets/{ticket_id}/status")
def update_ticket_status(
    ticket_id: str,
    status: str,
    db: Session = Depends(get_db),
):
    allowed_statuses = {"open", "in_progress", "resolved", "closed"}

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid ticket status. "
                f"Allowed statuses: {', '.join(sorted(allowed_statuses))}"
            ),
        )

    ticket = (
        db.query(SupportTicket)
        .filter(SupportTicket.ticket_id == ticket_id)
        .first()
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found.",
        )

    ticket.status = status
    db.commit()
    db.refresh(ticket)

    return {
        "message": "Ticket status updated.",
        "ticket": ticket_to_dict(ticket),
    }


@router.get("/knowledge/search")
def knowledge_search(
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
def knowledge_vector_search(
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