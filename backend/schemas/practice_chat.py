from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="system | user | assistant")
    content: str


class PracticeChatRequest(BaseModel):
    messages: list[ChatMessage]
    scenario_title: str | None = None


class PracticeChatResponse(BaseModel):
    reply: str
