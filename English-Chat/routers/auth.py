"""
账号管理API - 登录注册
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from service.agent import get_agent_service, ChatAgent

from service.database import get_db
from crud.users import (
    db_create_user,
    db_get_user_by_name,
    db_authenticate_user,
    db_create_token,
    db_delete_token,
    db_get_token_by_user_id,
    db_set_user_online,
    db_get_user_by_user_id,
)

from crud.users import RegisterRequest, LoginRequest
from utils.response import success_response
from utils.security import check_password_complexity
from utils.auth import get_current_user

router = APIRouter(prefix="/api/account", tags=["账号"])

@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册：必填姓名、英语水平、年龄、职业、兴趣爱好；选填目标、习惯、偏好。"""
    username = req.username
    password = req.password
    password_confirm = req.password_confirm

    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名和密码不能为空")
    if not (req.name or "").strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请填写姓名")
    if not (req.english_level or "").strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请选择英语水平")
    if req.age is None or req.age < 1 or req.age > 150:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请填写有效年龄（1-150）")
    if not (req.occupation or "").strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请填写职业")
    if not (req.interests or "").strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请填写兴趣爱好")

    # 检查密码确认
    if password != password_confirm:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="两次输入的密码不一致")

    # 检查用户是否存在
    existing_user = await db_get_user_by_name(db, username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已存在")
    
    # 验证密码复杂度
    is_ok, detail = check_password_complexity(password)
    if not is_ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    # 创建用户
    user = await db_create_user(db, req)
    token = await db_create_token(db, user.id)
    
    return success_response(
        message="注册成功",
        data={
            "token": token,
            "account_name": user.username
        }
    )

@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db), agent: ChatAgent = Depends(get_agent_service)):
    """用户登录"""
    username = req.username
    password = req.password
    
    user = await db_authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    
    token = await db_create_token(db, user.id)
    # 标记用户在线
    await db_set_user_online(db, user.id, True)
    user = await db_get_user_by_user_id(db, user.id)
    await agent.cache.set(token, user.id)
    await agent.cache.set(str(user.id), user.to_dict())

    return success_response(
        message="登录成功",
        data={
            "token": token,
            "account_name": username,
            "user_id": user.id
        }
    )

@router.post("/logout")
async def logout(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db), agent: ChatAgent = Depends(get_agent_service)):
    """用户登出"""
    user_id = user.get("id", None)
    await db_set_user_online(db, user_id, False)
    token = await db_get_token_by_user_id(db, user_id)
    await db_delete_token(db, user_id)

    await agent.cache.delete(token)
    await agent.cache.delete(str(user_id))

    return success_response(message="已退出账号")


@router.get("/current")
async def get_me(user: dict = Depends(get_current_user)):
    """获取当前用户信息。user_profile 中含 is_admin（按 username 判断，仅 admin 为管理员），供前端判断是否显示用户管理入口。"""
    is_admin = user.get("username") == "admin"
    profile = {**user, "is_admin": is_admin}
    return success_response(
        message="获取用户信息成功",
        data={"user_profile": profile},
    )