from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse
from app.services.handoff import classify_issue_type, should_handoff_to_human
from app.tools.order_tools import check_order_status, extract_order_id
from app.tools.ticket_tools import create_support_ticket


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
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

    return ChatResponse(
        reply=f"You said: {request.message}",
        needs_human_handoff=False,
    )