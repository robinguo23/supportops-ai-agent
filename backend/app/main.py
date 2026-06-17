import re
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(
    title="SupportOps AI Agent API",
    description="Minimal backend API for the SupportOps AI Agent project.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    needs_human_handoff: bool = False
    tool_used: str | None = None
    tool_result: dict | None = None


HANDOFF_KEYWORDS = [
    "refund",
    "complaint",
    "angry",
    "human",
    "manager",
    "cancel",
    "charged twice",
    "wrong item",
]


MOCK_ORDERS = {
    "ORD-1001": {
        "status": "shipped",
        "estimated_delivery": "2026-06-20",
        "carrier": "Royal Mail",
    },
    "ORD-1002": {
        "status": "processing",
        "estimated_delivery": "2026-06-23",
        "carrier": "DPD",
    },
    "ORD-1003": {
        "status": "delivered",
        "estimated_delivery": "2026-06-15",
        "carrier": "Evri",
    },
}


MOCK_TICKETS: list[dict] = []


def should_handoff_to_human(message: str) -> bool:
    normalized_message = message.lower()
    return any(keyword in normalized_message for keyword in HANDOFF_KEYWORDS)


def classify_issue_type(message: str) -> str:
    normalized_message = message.lower()

    if "refund" in normalized_message:
        return "refund_request"

    if "complaint" in normalized_message or "angry" in normalized_message:
        return "complaint"

    if "cancel" in normalized_message:
        return "cancellation"

    if "wrong item" in normalized_message:
        return "wrong_item"

    if "charged twice" in normalized_message:
        return "billing_issue"

    if "human" in normalized_message or "manager" in normalized_message:
        return "human_support_request"

    return "general_support"


def extract_order_id(message: str) -> str | None:
    match = re.search(r"ORD-\d{4}", message.upper())
    if match:
        return match.group(0)
    return None


def check_order_status(order_id: str) -> dict:
    order = MOCK_ORDERS.get(order_id)

    if order is None:
        return {
            "found": False,
            "order_id": order_id,
        }

    return {
        "found": True,
        "order_id": order_id,
        **order,
    }


def create_support_ticket(issue_type: str, summary: str) -> dict:
    ticket_id = f"TCK-{len(MOCK_TICKETS) + 1001}"

    ticket = {
        "ticket_id": ticket_id,
        "issue_type": issue_type,
        "summary": summary,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    MOCK_TICKETS.append(ticket)
    return ticket


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "supportops-ai-agent-backend",
    }


@app.post("/chat", response_model=ChatResponse)
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
                f"I have created support ticket {ticket['ticket_id']} for a human agent to review."
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
                f"I have created support ticket {ticket['ticket_id']} for a human support agent."
            ),
            needs_human_handoff=True,
            tool_used="create_support_ticket",
            tool_result=ticket,
        )

    return ChatResponse(
        reply=f"You said: {request.message}",
        needs_human_handoff=False,
    )