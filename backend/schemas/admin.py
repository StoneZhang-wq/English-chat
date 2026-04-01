from __future__ import annotations

from pydantic import BaseModel, Field


class AdminUpdateUserRequest(BaseModel):
    email: str | None = None
    name: str | None = None
    english_level: str | None = None
    age: int | None = None
    occupation: str | None = None
    goals: str | None = None
    habits: str | None = None
    interests: str | None = None
    preferences: str | None = None
    password: str | None = Field(default=None, min_length=8)
    is_admin: bool | None = None
