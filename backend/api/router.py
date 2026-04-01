"""Central router registration."""
from __future__ import annotations

from fastapi import APIRouter

from api.routes import account, admin, practice_chat


def build_api_router() -> APIRouter:
    router = APIRouter(prefix="/api")
    router.include_router(practice_chat.router)
    router.include_router(account.router)
    router.include_router(admin.router)
    return router
