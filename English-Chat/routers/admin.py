from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from service.database import get_db
from crud.users import (
    db_list_users_paginated,
    db_count_users,
    db_count_online_users,
    db_update_user,
    db_get_user_by_user_id,
    db_delete_user,
    UpdateRequest,
)
from utils.response import success_response
from utils.auth import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users/stats")
async def get_user_stats(
    admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    search: str = Query(None, description="按账号模糊搜索时的关键词，仅影响 total 是否按搜索过滤"),
):
    """获取总用户数与在线用户数（仅管理员）。可选 search 时 total 为匹配数量。"""
    total = await db_count_users(db, search)
    online = await db_count_online_users(db)
    return success_response(
        message="获取统计成功",
        data={"total": total, "online": online},
    )


@router.get("/users")
async def list_users(
    admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(100, ge=1, le=100, description="每页条数，最多 100"),
    search: str = Query(None, description="按用户账号模糊搜索"),
):
    """分页获取用户列表，支持按账号模糊搜索（仅管理员）"""
    users, total = await db_list_users_paginated(db, offset=offset, limit=limit, search=search)
    user_list = [u.to_dict() for u in users]
    return success_response(
        message="获取用户列表成功",
        data={"items": user_list, "total": total},
    )


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UpdateRequest,
    admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新用户信息（账号、密码、昵称、邮箱等，仅管理员）"""
    updated_user = await db_update_user(db, user_id, user_data)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return success_response(message="更新用户信息成功", data=updated_user.to_dict())


@router.delete("/users/{user_id}")
async def delete_user(user_id: int,
                      admin: dict = Depends(get_current_admin),
                      db: AsyncSession = Depends(get_db)):
    # 禁止删除自己
    if user_id == admin.get("id", None):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不能删除管理员自己")

    # 检查用户是否存在
    user = await db_get_user_by_user_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    success = await db_delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除失败")

    return success_response(message="用户删除成功", data=None)