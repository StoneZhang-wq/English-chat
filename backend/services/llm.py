"""Compatibility export. Prefer `services.llm.llm_client`."""
from services.llm.llm_client import chat_completion

__all__ = ["chat_completion"]
