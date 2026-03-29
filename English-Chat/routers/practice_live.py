import json
import asyncio
import base64
import aiofiles
import os
import time
import uuid
from types import SimpleNamespace
from starlette import status
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request, Header
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Optional, Any
import aiohttp
from config import configer
from crud.chat import db_create_chat_session, db_add_chat_message, db_list_chat_messages
from models import ChatMessage
from service.agent import ChatAgent, get_agent_service
from utils.auth import get_current_user
from utils import logger
from utils.response import success_response
from models.base import SceneType
from utils.tools import read_file
from service.database import get_db
from service.scene_manager import (
    get_unlocked_small_scene_ids,
    get_one_immersive_dialogue_for_scene,
    get_one_random_immersive_dialogue,
)


router = APIRouter(prefix="/api/practice-live", tags=["practice-live"])

# --- 真人 1v1 练习：解锁场景列表 + 按场景取一条对话（角色/任务/台词）---
@router.get("/unlocked-scenes")
async def api_practice_live_unlocked_scenes(
    request: Request,
    account_name: str = None,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
    agent: ChatAgent = Depends(get_agent_service),
):
    """
    返回当前账号已解锁的 small_scene_id 列表，供匹配时取交集/并集选主题。

    在当前架构下，基于 npc_learn_progress 表与 scene_manager.get_unlocked_small_scene_ids，
    不再使用 English-chat-ai 中的本地 scene_npc_db。
    """
    # 统一改为标准 token 认证：前端必须携带 Authorization: Bearer <token>
    # 不再使用 account_name 作为认证依据（该参数仅为兼容旧前端，忽略即可）。
    if not authorization or not isinstance(authorization, str) or not authorization.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    user = await get_current_user(authorization=authorization, db=db, agent=agent)
    ids = await get_unlocked_small_scene_ids(db, agent, int((user or {}).get("id")))
    return JSONResponse({"small_scene_ids": ids})


def _practice_live_dialogue_response(d):
    """将一条 immersive 对话转为 1v1 前端需要的 JSON 结构。"""
    if not d:
        return None
    content = d.get("content") or []
    npc_name = (d.get("npc_name") or "").strip() or "角色A"
    role_label_a = npc_name
    role_label_b = "学习者"
    lines_a = [x for x in content if x.get("role") == "A"]
    lines_b = [x for x in content if x.get("role") == "B"]
    return {
        "small_scene_id": d.get("small_scene"),
        "small_scene_name": d.get("small_scene_name"),
        "npc_name": npc_name,
        "role_label_a": role_label_a,
        "role_label_b": role_label_b,
        "task_a": d.get("user_goal_a") or d.get("core_sentences") or "",
        "task_b": d.get("user_goal") or d.get("core_sentences") or "",
        "core_sentences": d.get("core_sentences"),
        "lines_a": [{"content": x.get("content"), "hint": x.get("hint")} for x in lines_a],
        "lines_b": [{"content": x.get("content"), "hint": x.get("hint")} for x in lines_b],
    }


@router.get("/dialogue")
async def api_practice_live_dialogue(
    request: Request,
    small_scene_id: str = None,
    room_id: str = None,
    db: AsyncSession = Depends(get_db),
    agent: ChatAgent = Depends(get_agent_service),
):
    """
    返回该小场景下一条沉浸式对话；room_id 相同时返回同一条，保证同一房间两人同一主题。

    在当前架构中，基于 scene_manager.get_dialogues 过滤 usage=immersive，而非本地 JSON。
    """
    seed = (room_id or "").strip() or None
    if small_scene_id and small_scene_id.strip():
        d = await get_one_immersive_dialogue_for_scene(db, agent, small_scene_id.strip(), seed=seed)
    else:
        d = await get_one_random_immersive_dialogue(db, agent, seed=seed)
    if not d:
        return JSONResponse({"error": "no dialogue for scene"}, status_code=404)
    out = _practice_live_dialogue_response(d)
    return JSONResponse(out)


@router.get("/dialogue/random")
async def api_practice_live_dialogue_random(
    request: Request,
    room_id: str = None,
    db: AsyncSession = Depends(get_db),
    agent: ChatAgent = Depends(get_agent_service),
):
    """返回任意一条 immersive 对话；room_id 相同时返回同一条，保证同一房间两人同一主题。"""
    seed = (room_id or "").strip() or None
    d = await get_one_random_immersive_dialogue(db, agent, seed=seed)
    if not d:
        return JSONResponse({"error": "no immersive dialogue"}, status_code=404)
    out = _practice_live_dialogue_response(d)
    return JSONResponse(out)


@router.get("/config")
async def api_practice_live_config():
    """返回 1v1 前端运行时配置（如 Varta 后端地址），避免构建时写死。主站配置 VARTA_BACKEND_URL 后无需重构建 1v1 即可生效。"""
    base = (os.getenv("VARTA_BACKEND_URL") or "").strip().rstrip("/")
    return JSONResponse({"backendUrl": base})


@router.get("/user-count")
async def api_practice_live_user_count():
    """代理 Varta 后端的 /user-count，避免前端直连 Varta 时的 CORS 问题。主站需配置 VARTA_BACKEND_URL。"""
    base = (os.getenv("VARTA_BACKEND_URL") or "").strip().rstrip("/")
    if not base:
        return JSONResponse({"userCount": 0})
    url = f"{base}/user-count"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return JSONResponse({"userCount": 0})
                data = await resp.json()
                return JSONResponse(data)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("practice-live user-count proxy failed: %s", e)
        return JSONResponse({"userCount": 0})
