from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str
    password: str
    password_confirm: str
    email: str | None = None
    name: str | None = None
    english_level: str | None = "beginner"
    age: int | None = None
    occupation: str | None = None
    goals: str | None = None
    habits: str | None = None
    interests: str | None = None
    preferences: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UpdateProfileRequest(BaseModel):
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
