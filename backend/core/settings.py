"""Application settings loader (object-based, no config globals)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)


def _get_env_str(key: str, default: str) -> str:
    value = os.getenv(key)
    if value is None or not value.strip():
        return default
    return value.strip()


def _get_env_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None or not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


@dataclass
class Settings:
    server_host: str = "0.0.0.0"
    server_port: int = 8088
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"


def load_settings() -> Settings:
    _load_env()
    return Settings(
        server_host=_get_env_str("SERVER_HOST", "0.0.0.0"),
        server_port=_get_env_int("SERVER_PORT", 8088),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=_get_env_str("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        openai_model=_get_env_str("OPENAI_MODEL", "gpt-3.5-turbo"),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()
