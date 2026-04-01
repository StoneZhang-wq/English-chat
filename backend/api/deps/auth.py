from __future__ import annotations

from fastapi import HTTPException, status

from services.user_service import user_service


def extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少 Authorization")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization 格式错误")
    return parts[1].strip()


async def get_current_user(authorization: str | None) -> dict:
    token = extract_bearer(authorization)
    user = await user_service.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态已失效")
    return user


async def ensure_admin(authorization: str | None) -> dict:
    user = await get_current_user(authorization)
    if not user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问")
    return user
