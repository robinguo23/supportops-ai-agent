from typing import Any
from pydantic import BaseModel

# 定义数据格式 frontend 发什么数据格式过来
class ChatRequest(BaseModel):
    message: str

# 后段 返回前段 什么数据格式
class ChatResponse(BaseModel):
    reply: str
    needs_human_handoff: bool = False
    tool_used: str | None = None
    tool_result: dict[str, Any] | None = None