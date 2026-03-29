"""Practice 场景文字对话：转发豆包（OpenAI 兼容）。"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.llm import chat_completion

logger = logging.getLogger(__name__)

router = APIRouter(tags=["practice"])


class ChatMessage(BaseModel):
    role: str = Field(..., description="system | user | assistant")
    content: str


class PracticeChatRequest(BaseModel):
    messages: list[ChatMessage]
    scenario_title: str | None = None


class PracticeChatResponse(BaseModel):
    reply: str


def _build_system_prompt(scenario_title: str | None) -> str:
    base = (
        "You are a friendly English conversation tutor for role-play practice. "
        "Reply mainly in English. Keep responses concise and suitable for spoken dialogue. "
        "If the learner writes in Chinese, you may briefly clarify in English."
    )
    if scenario_title:
        base += f" Current scenario theme: {scenario_title}."
    return base


@router.post("/practice/chat", response_model=PracticeChatResponse)
async def practice_chat(body: PracticeChatRequest) -> PracticeChatResponse:
    if not body.messages:
        raise HTTPException(status_code=400, detail="messages 不能为空")

    system = _build_system_prompt(body.scenario_title)
    # 仅允许 user/assistant 历史 + 服务端注入 system
    openai_messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for m in body.messages:
        r = m.role.lower().strip()
        if r not in ("user", "assistant"):
            continue
        openai_messages.append({"role": r, "content": m.content})

    if len(openai_messages) <= 1:
        raise HTTPException(status_code=400, detail="至少需要一条 user 或 assistant 消息")

    try:
        reply = await chat_completion(openai_messages)
        return PracticeChatResponse(reply=reply)
    except RuntimeError as e:
        logger.exception("practice_chat failed")
        raise HTTPException(status_code=503, detail=str(e)) from e
