from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(
    title="SupportOps AI Agent API",
    description="Minimal backend API for the SupportOps AI Agent project.",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    needs_human_handoff: bool = False


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "supportops-ai-agent-backend",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return ChatResponse(
        reply=f"You said: {request.message}",
        needs_human_handoff=False,
    )