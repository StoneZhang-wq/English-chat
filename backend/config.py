"""从环境变量加载配置（变量名与 English-Chat 一致，便于共用 .env）。"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)


def _get_str(key: str, default: str | None = None) -> str | None:
    v = os.getenv(key)
    if v is None or v.strip() == "":
        return default
    return v.strip()


OPENAI_API_KEY: str | None = _get_str("OPENAI_API_KEY")
OPENAI_BASE_URL: str = (_get_str("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL: str = _get_str("OPENAI_MODEL") or "gpt-3.5-turbo"

SERVER_HOST: str = _get_str("SERVER_HOST") or "0.0.0.0"
SERVER_PORT: int = int(_get_str("SERVER_PORT") or "8088")
