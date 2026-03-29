import uuid
from datetime import datetime, timedelta

import json
from starlette import status
from fastapi import HTTPException
from sqlalchemy import select, update, desc, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User, UserToken
from utils import security
from utils.security import check_password_complexity
from typing import Optional
from pydantic import BaseModel
from utils import logger

# 前端英语水平选项（入门/初级/中级/高级）与数据库存储值映射
ENGLISH_LEVEL_DISPLAY_TO_DB = {
    "入门": "minimal",
    "初级": "beginner",
    "中级": "intermediate",
    "高级": "advanced",
}


class RegisterRequest(BaseModel):
    username: str
    password: str
    password_confirm: str = None
    email: Optional[str] = None
    # 必填
    name: Optional[str] = None
    english_level: Optional[str] = None  # 前端传 入门/初级/中级/高级，入库前映射为 minimal/beginner/intermediate/advanced
    age: Optional[int] = None
    occupation: Optional[str] = None
    interests: Optional[str] = None
    # 选填
    goals: Optional[str] = None
    habits: Optional[str] = None
    preferences: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str

class UpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    # 管理员编辑用户资料时可更新以下字段
    name: Optional[str] = None
    email: Optional[str] = None


def update_user_profile(user_profile: dict, test_json: Optional[str]):
    # 尝试解析JSON
    has_updated = False
    try:
        new_info = json.loads(test_json)
        if new_info.get("name") and not user_profile.get("name"):
            user_profile["name"] = new_info["name"]
            has_updated = True

        if new_info.get("age") and not user_profile.get("age"):
            user_profile["age"] = int(new_info["age"])
            has_updated = True

        if new_info.get("occupation") and not user_profile.get("occupation"):
            user_profile["occupation"] = new_info["occupation"]
            has_updated = True

        if new_info.get("interests"):
            if user_profile.get("interests"):
                user_profile["interests"] = user_profile["interests"] + "，" + new_info["interests"]
            else:
                user_profile["interests"] = new_info["interests"]
                has_updated = True

        if new_info.get("goals"):
            user_profile["goals"] = new_info["goals"]
            has_updated = True

        if new_info.get("habits"):
            if user_profile.get("habits"):
                user_profile["habits"] = user_profile["habits"] + "，" + new_info["habits"]
            else:
                user_profile["habits"] = new_info["habits"]
                has_updated = True

        if new_info.get("preferences"):
            if user_profile.get("preferences"):
                user_profile["preferences"] = user_profile["preferences"] + "，" + new_info["preferences"]
            else:
                user_profile["preferences"] = new_info["preferences"]
                has_updated = True

    except Exception as e:
        logger.error(f"生成的用户摘要json信息有误: {test_json}")
        return None

    if not has_updated:
        return None

    return user_profile


# 创建用户（含注册时填写的姓名、英语水平、年龄、职业、兴趣爱好等，写入用户表）
async def db_create_user(db: AsyncSession, user_data: RegisterRequest):
    hashed_password = security.get_hash_password(user_data.password)
    english_level_db = ENGLISH_LEVEL_DISPLAY_TO_DB.get(
        (user_data.english_level or "").strip(), "beginner"
    )
    user = User(
        email=user_data.email,
        username=user_data.username,
        password=hashed_password,
        name=(user_data.name or "").strip() or None,
        english_level=english_level_db,
        age=user_data.age if user_data.age is not None else 24,
        occupation=(user_data.occupation or "").strip() or None,
        interests=(user_data.interests or "").strip() or None,
        goals=(user_data.goals or "").strip() or None,
        habits=(user_data.habits or "").strip() or None,
        preferences=(user_data.preferences or "").strip() or None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def db_delete_user(db: AsyncSession, user_id: int):
    stmt = delete(User).where(User.id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


# 根据用户名查询数据库
async def db_get_user_by_name(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 根据用户id获取用户
async def db_get_user_by_user_id(db: AsyncSession, user_id: int):
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 生成 Token
async def db_create_token(db: AsyncSession, user_id: int):
    # 生成 Token + 设置过期时间 → 查询数据库当前用户是否有 Token → 有：更新；没有：添加
    token = str(uuid.uuid4())
    # timedelta(days=7, hours=2, minutes=30, seconds=10)
    expires_at = datetime.now() + timedelta(days=0, hours=4)
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()

    if user_token:
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)
        await db.commit()

    return token


async def db_authenticate_user(db: AsyncSession, username: str, password: str):
    user = await db_get_user_by_name(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.password):
        return None

    return user


# 根据 Token 查询用户：验证 Token → 查询用户
async def db_get_user_by_token(db: AsyncSession, token: str):
    query = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.expires_at < datetime.now():
        return None

    query = select(User).where(User.id == db_token.user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def db_get_token_by_user_id(db: AsyncSession, user_id: int):
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.expires_at < datetime.now():
        return None

    return db_token.token


async def db_delete_token(db: AsyncSession, user_id: int):
    stmt = delete(UserToken).where(UserToken.user_id == user_id)
    await db.execute(stmt)
    await db.commit()


async def db_list_all_users(db: AsyncSession):
    """获取所有用户（按创建时间倒序）"""
    query = select(User).order_by(desc(User.created_at))
    result = await db.execute(query)
    return result.scalars().all()


async def db_set_user_online(db: AsyncSession, user_id: int, is_online: bool):
    """设置用户在线状态（登录时 True，登出时 False）"""
    stmt = update(User).where(User.id == user_id).values(is_online=is_online)
    await db.execute(stmt)
    await db.commit()


async def db_list_users_paginated(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
):
    """
    分页获取用户列表，支持按账号模糊搜索。
    返回 (users, total_count)。
    """
    base = select(User)
    count_stmt = select(func.count()).select_from(User)
    if search and search.strip():
        term = f"%{search.strip()}%"
        base = base.where(User.username.ilike(term))
        count_stmt = count_stmt.where(User.username.ilike(term))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    query = base.order_by(desc(User.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return users, total


async def db_count_users(db: AsyncSession, search: Optional[str] = None) -> int:
    """统计用户总数，可选按账号模糊过滤"""
    stmt = select(func.count()).select_from(User)
    if search and search.strip():
        stmt = stmt.where(User.username.ilike(f"%{search.strip()}%"))
    result = await db.execute(stmt)
    return result.scalar() or 0


async def db_count_online_users(db: AsyncSession) -> int:
    """统计当前在线用户数"""
    stmt = select(func.count()).select_from(User).where(User.is_online == True)
    result = await db.execute(stmt)
    return result.scalar() or 0


async def db_update_user(db: AsyncSession, user_id: int, user_data: UpdateRequest):
    """更新用户信息：用户名、密码、昵称、邮箱等（管理员可编辑更多字段）"""
    values = {}
    if user_data.username is not None:
        values["username"] = user_data.username
    if user_data.name is not None:
        values["name"] = user_data.name
    if user_data.email is not None:
        values["email"] = user_data.email
    if user_data.password and user_data.password.strip():
        is_ok, detail = check_password_complexity(user_data.password)
        if not is_ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        values["password"] = security.get_hash_password(user_data.password)

    if not values:
        updated_user = await db_get_user_by_user_id(db, user_id)
        if not updated_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        return updated_user

    stmt = update(User).where(User.id == user_id).values(**values)
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 若修改了密码则刷新 token，使旧会话失效
    if user_data.password and user_data.password.strip():
        await db_create_token(db, user_id)

    updated_user = await db_get_user_by_user_id(db, user_id)
    return updated_user
