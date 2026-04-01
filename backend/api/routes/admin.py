"""Admin APIs for user management."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from api.deps.auth import ensure_admin
from schemas.admin import AdminUpdateUserRequest
from services.user_service import user_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.put("/users/{user_id}")
async def admin_update_user(
    user_id: int,
    body: AdminUpdateUserRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict:
    await ensure_admin(authorization)
    try:
        updated = await user_service.admin_update_user(user_id, body.model_dump(exclude_none=True))
    except ValueError as e:
        detail = str(e)
        code = 404 if detail == "用户不存在" else 400
        raise HTTPException(status_code=code, detail=detail) from e
    return {"status": "success", "message": "管理员更新用户信息成功", "user_profile": updated}


@router.get("/users")
async def list_users(authorization: str | None = Header(default=None, alias="Authorization")) -> dict:
    await ensure_admin(authorization)
    users = await user_service.list_users()
    return {"status": "success", "items": users, "total": len(users)}
