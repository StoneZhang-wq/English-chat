"""Persistence layer for users/tokens."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from models.user_tables import UserRow

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"


class UserRepository:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not USERS_FILE.exists():
            USERS_FILE.write_text('{"users":[],"tokens":[]}', encoding="utf-8")

    async def transaction_read(self) -> dict[str, Any]:
        async with self._lock:
            return self._read()

    async def transaction_write(self, data: dict[str, Any]) -> None:
        async with self._lock:
            self._write(data)

    async def with_lock(self, handler):
        async with self._lock:
            data = self._read()
            out = await handler(data)
            self._write(data)
            return out

    @staticmethod
    def find_user_by_name(data: dict[str, Any], username: str) -> UserRow | None:
        target = username.strip().lower()
        return next((u for u in data["users"] if str(u["username"]).lower() == target), None)

    @staticmethod
    def public_user(user: UserRow) -> dict[str, Any]:
        out = dict(user)
        out.pop("password_hash", None)
        return out

    @staticmethod
    def _read() -> dict[str, Any]:
        raw = USERS_FILE.read_text(encoding="utf-8")
        obj = json.loads(raw)
        obj.setdefault("users", [])
        obj.setdefault("tokens", [])
        return obj

    @staticmethod
    def _write(data: dict[str, Any]) -> None:
        USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


user_repository = UserRepository()
