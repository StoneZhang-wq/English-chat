"""User business service."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from repositories.user_repository import user_repository

TOKEN_EXPIRE_DAYS = 30


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_password(password: str, *, salt: str | None = None) -> str:
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_value.encode("utf-8"),
        120_000,
    ).hex()
    return f"{salt_value}${digest}"


def _verify_password(password: str, hashed: str) -> bool:
    if "$" not in hashed:
        return False
    salt, expected = hashed.split("$", 1)
    actual = _hash_password(password, salt=salt).split("$", 1)[1]
    return hmac.compare_digest(expected, actual)


def _is_password_valid(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "密码长度不能少于8位"
    if not any(c.isalpha() for c in password):
        return False, "密码必须包含至少一个字母"
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含至少一个数字"
    return True, ""


class UserService:
    async def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        async def handler(data: dict[str, Any]) -> dict[str, Any]:
            username = str(payload.get("username", "")).strip()
            password = str(payload.get("password", "")).strip()
            password_confirm = str(payload.get("password_confirm", "")).strip()
            if not username or not password:
                raise ValueError("用户名和密码不能为空")
            if password != password_confirm:
                raise ValueError("两次输入的密码不一致")
            ok, detail = _is_password_valid(password)
            if not ok:
                raise ValueError(detail)
            if user_repository.find_user_by_name(data, username):
                raise ValueError("用户已存在")

            user_id = (max((u["id"] for u in data["users"]), default=0) + 1) if data["users"] else 1
            is_admin = username.lower() == "admin"
            now_iso = _utcnow().isoformat()
            user = {
                "id": user_id,
                "username": username,
                "password_hash": _hash_password(password),
                "email": (payload.get("email") or "").strip() or None,
                "name": (payload.get("name") or "").strip() or None,
                "english_level": (payload.get("english_level") or "beginner").strip(),
                "age": payload.get("age"),
                "occupation": (payload.get("occupation") or "").strip() or None,
                "goals": (payload.get("goals") or "").strip() or None,
                "habits": (payload.get("habits") or "").strip() or None,
                "interests": (payload.get("interests") or "").strip() or None,
                "preferences": (payload.get("preferences") or "").strip() or None,
                "is_online": False,
                "is_admin": is_admin,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            data["users"].append(user)
            return user_repository.public_user(user)

        return await user_repository.with_lock(handler)

    async def login(self, username: str, password: str) -> tuple[str, dict[str, Any]]:
        async def handler(data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
            user = user_repository.find_user_by_name(data, username)
            if not user or not _verify_password(password, user["password_hash"]):
                raise ValueError("用户名或密码错误")
            user["is_online"] = True
            user["updated_at"] = _utcnow().isoformat()
            token = secrets.token_urlsafe(32)
            expire = (_utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)).isoformat()
            data["tokens"] = [t for t in data["tokens"] if t["user_id"] != user["id"]]
            data["tokens"].append({"token": token, "user_id": user["id"], "expires_at": expire})
            return token, user_repository.public_user(user)

        return await user_repository.with_lock(handler)

    async def get_user_by_token(self, token: str) -> dict[str, Any] | None:
        async def handler(data: dict[str, Any]) -> dict[str, Any] | None:
            rec = next((t for t in data["tokens"] if t["token"] == token), None)
            if not rec:
                return None
            if datetime.fromisoformat(rec["expires_at"]) <= _utcnow():
                data["tokens"] = [t for t in data["tokens"] if t["token"] != token]
                return None
            user = next((u for u in data["users"] if u["id"] == rec["user_id"]), None)
            if not user:
                return None
            return user_repository.public_user(user)

        return await user_repository.with_lock(handler)

    async def update_self(self, user_id: int, updates: dict[str, Any]) -> dict[str, Any]:
        return await self._update_user(user_id, updates, allow_role_change=False)

    async def admin_update_user(self, user_id: int, updates: dict[str, Any]) -> dict[str, Any]:
        return await self._update_user(user_id, updates, allow_role_change=True)

    async def list_users(self) -> list[dict[str, Any]]:
        async def handler(data: dict[str, Any]) -> list[dict[str, Any]]:
            return [user_repository.public_user(u) for u in data["users"]]

        return await user_repository.with_lock(handler)

    async def _update_user(self, user_id: int, updates: dict[str, Any], *, allow_role_change: bool) -> dict[str, Any]:
        async def handler(data: dict[str, Any]) -> dict[str, Any]:
            user = next((u for u in data["users"] if u["id"] == user_id), None)
            if not user:
                raise ValueError("用户不存在")

            editable_fields = {
                "email",
                "name",
                "english_level",
                "age",
                "occupation",
                "goals",
                "habits",
                "interests",
                "preferences",
            }
            for key in editable_fields:
                if key in updates:
                    user[key] = updates[key]
            if "password" in updates and updates["password"]:
                ok, detail = _is_password_valid(str(updates["password"]))
                if not ok:
                    raise ValueError(detail)
                user["password_hash"] = _hash_password(str(updates["password"]))
            if allow_role_change and "is_admin" in updates:
                user["is_admin"] = bool(updates["is_admin"])

            user["updated_at"] = _utcnow().isoformat()
            return user_repository.public_user(user)

        return await user_repository.with_lock(handler)


user_service = UserService()
