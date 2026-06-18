from typing import Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    needs_human_handoff: bool = False
    tool_used: str | None = None
    tool_result: dict[str, Any] | None = None