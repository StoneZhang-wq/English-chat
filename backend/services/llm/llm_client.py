"""OpenAI-compatible LLM client."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from core.settings import get_settings

logger = logging.getLogger(__name__)

TIMEOUT = 120.0


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.4,
    max_tokens: int = 2048,
) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY 未配置，请在 backend/.env 中设置（可与 English-Chat 共用）")

    url = f"{settings.openai_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": settings.openai_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(url, headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            body = resp.text
            logger.error("LLM HTTP %s: %s", resp.status_code, body[:2000])
            raise RuntimeError(f"LLM 请求失败: {resp.status_code}") from None
        data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        logger.error("Unexpected LLM response: %s", data)
        raise RuntimeError("LLM 响应格式异常") from e
