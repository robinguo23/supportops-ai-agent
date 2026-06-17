import re
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


def should_handoff_to_human(message: str) -> bool:
    normalized_message = message.lower()
    return any(keyword in normalized_message for keyword in HANDOFF_KEYWORDS)


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

        return ChatResponse(
            reply=(
                f"I could not find order {order_id}. "
                "Please check the order number or contact human support."
            ),
            needs_human_handoff=True,
            tool_used="check_order_status",
            tool_result=tool_result,
        )

    needs_handoff = should_handoff_to_human(request.message)

    if needs_handoff:
        return ChatResponse(
            reply=(
                "I understand this may need extra support. "
                "I will flag this conversation for a human support agent."
            ),
            needs_human_handoff=True,
        )

    return ChatResponse(
        reply=f"You said: {request.message}",
        needs_human_handoff=False,
    )