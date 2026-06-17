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


def should_handoff_to_human(message: str) -> bool:
    normalized_message = message.lower()
    return any(keyword in normalized_message for keyword in HANDOFF_KEYWORDS)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "supportops-ai-agent-backend",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
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