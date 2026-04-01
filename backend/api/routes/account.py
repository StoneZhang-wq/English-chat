"""Account APIs: register/login/current/profile update."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from api.deps.auth import get_current_user
from schemas.account import LoginRequest, RegisterRequest, UpdateProfileRequest
from services.user_service import user_service

router = APIRouter(prefix="/account", tags=["account"])


@router.post("/register")
async def register(body: RegisterRequest) -> dict:
    try:
        user = await user_service.register(body.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"status": "success", "message": "注册成功", "user": user}


@router.post("/login")
async def login(body: LoginRequest) -> dict:
    try:
        token, user = await user_service.login(body.username.strip(), body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    return {
        "status": "success",
        "message": "登录成功",
        "token": token,
        "account_name": user["username"],
        "user_profile": user,
    }


@router.get("/current")
async def current_user(authorization: str | None = Header(default=None, alias="Authorization")) -> dict:
    user = await get_current_user(authorization)
    return {"status": "success", "account_name": user["username"], "user_profile": user}


@router.put("/profile")
async def update_profile(
    body: UpdateProfileRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict:
    user = await get_current_user(authorization)
    updates = body.model_dump(exclude_none=True)
    try:
        updated = await user_service.update_self(user["id"], updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"status": "success", "message": "用户信息更新成功", "user_profile": updated}
