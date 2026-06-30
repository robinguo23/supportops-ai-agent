from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.chat import ChatRequest, ChatResponse
from app.services.embedding_service import generate_query_embedding
from app.services.handoff import classify_issue_type, should_handoff_to_human
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
                tool_result=tool_result,
            )

        ticket = create_support_ticket(
            db=db,
            issue_type="missing_order",
            summary=f"Customer asked about unknown order ID: {order_id}",
        )

        return ChatResponse(
            reply=(
                f"I could not find order {order_id}. "
                f"I have created support ticket {ticket['ticket_id']} "
                "for a human agent to review."
            ),
            needs_human_handoff=True,
            tool_used="create_support_ticket",
            tool_result=ticket,
        )

    needs_handoff = should_handoff_to_human(request.message)

    if needs_handoff:
        issue_type = classify_issue_type(request.message)

        ticket = create_support_ticket(
            db=db,
            issue_type=issue_type,
            summary=request.message,
        )

        return ChatResponse(
            reply=(
                "I understand this may need extra support. "
                f"I have created support ticket {ticket['ticket_id']} "
                "for a human support agent."
            ),
            needs_human_handoff=True,
            tool_used="create_support_ticket",
            tool_result=ticket,
        )

    query_embedding = generate_query_embedding(request.message)

    knowledge_chunks = search_knowledge_chunks_by_embedding(
        db=db,
        query_embedding=query_embedding,
        limit=3,
    )

    if knowledge_chunks:
        top_chunk = knowledge_chunks[0]

        sources = [
            {
                "document_id": chunk["document_id"],
                "title": chunk["title"],
                "source": chunk["source"],
                "similarity": chunk["similarity"],
            }
            for chunk in knowledge_chunks
        ]

        return ChatResponse(
            reply=(
                "Based on our support policy:\n\n"
                f"{top_chunk['content']}"
            ),
            needs_human_handoff=False,
            tool_used="knowledge_vector_search",
            tool_result={
                "matched_chunks": knowledge_chunks,
                "sources": sources,
            },
        )

    knowledge_result = search_knowledge_base(request.message)

    if knowledge_result:
        return ChatResponse(
            reply=knowledge_result["answer"],
            needs_human_handoff=False,
            tool_used="knowledge_base_search",
            tool_result=knowledge_result,
        )

    return ChatResponse(
        reply=f"You said: {request.message}",
        needs_human_handoff=False,
    )


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