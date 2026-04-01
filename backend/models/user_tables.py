"""User-related table structures (logical model layer)."""
from __future__ import annotations

from typing import TypedDict


class UserRow(TypedDict, total=False):
    id: int
    username: str
    password_hash: str
    email: str | None
    name: str | None
    english_level: str
    age: int | None
    occupation: str | None
    goals: str | None
    habits: str | None
    interests: str | None
    preferences: str | None
    is_online: bool
    is_admin: bool
    created_at: str
    updated_at: str


class UserTokenRow(TypedDict):
    token: str
    user_id: int
    expires_at: str
