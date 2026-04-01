"""Practice text chat APIs."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from schemas.practice_chat import PracticeChatRequest, PracticeChatResponse
from services.llm.llm_client import chat_completion

logger = logging.getLogger(__name__)

router = APIRouter(tags=["practice"])

MAX_HISTORY_MESSAGES = 40
MAX_MESSAGE_CHARS = 4000


def _build_system_prompt(scenario_title: str | None) -> str:
    base = (
        "You are a friendly English conversation tutor for role-play practice. "
        "Reply mainly in English. Keep responses concise and suitable for spoken dialogue. "
        "If the learner writes in Chinese, you may briefly clarify in English."
    )
    if scenario_title:
        base += f" Current scenario theme: {scenario_title}."
    return base


def _to_openai_messages(body: PracticeChatRequest) -> list[dict[str, str]]:
    system = _build_system_prompt(body.scenario_title)
    normalized: list[dict[str, str]] = [{"role": "system", "content": system}]
    for m in body.messages[-MAX_HISTORY_MESSAGES:]:
        role = m.role.lower().strip()
        if role not in ("user", "assistant"):
            continue
        content = (m.content or "").strip()
        if not content:
            continue
        normalized.append({"role": role, "content": content[:MAX_MESSAGE_CHARS]})
    return normalized


@router.post("/practice/chat", response_model=PracticeChatResponse)
async def practice_chat(body: PracticeChatRequest) -> PracticeChatResponse:
    if not body.messages:
        raise HTTPException(status_code=400, detail="messages 不能为空")

    openai_messages = _to_openai_messages(body)
    if len(openai_messages) <= 1:
        raise HTTPException(status_code=400, detail="至少需要一条 user 或 assistant 消息")

    try:
        reply = await chat_completion(openai_messages)
        return PracticeChatResponse(reply=reply)
    except RuntimeError as e:
        logger.exception("practice_chat failed")
        raise HTTPException(status_code=503, detail=str(e)) from e
