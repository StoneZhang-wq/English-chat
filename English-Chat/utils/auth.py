from fastapi import Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from service.database import get_db
from service.agent import get_agent_service, ChatAgent
from crud import users


# 整合 根据 Token 查询用户，返回用户
async def get_current_user(
        authorization: str = Header(..., alias="Authorization"),
        db: AsyncSession = Depends(get_db),
        agent: ChatAgent = Depends(get_agent_service)
) -> dict:

    token = authorization.replace("Bearer ", "")
    user_id = await agent.cache.get(token)
    if user_id:
        user = await agent.cache.get(str(user_id))
        if user:
            return user

    user = await users.db_get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌或已经过期的令牌")

    await agent.cache.set(token, user.id)
    await agent.cache.set(str(user.id), user.to_dict())
    return user.to_dict()


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """仅当当前用户为管理员时通过：通过 username 判断，仅账号为 admin 时为管理员"""
    if current_user.get("username") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可执行此操作")
    return current_user