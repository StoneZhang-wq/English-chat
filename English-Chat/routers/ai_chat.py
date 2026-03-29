import json
import re
import asyncio
import base64
import aiofiles
import os
import uuid
from starlette import status
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from crud.chat import db_list_chat_messages
from crud.users import update_user_profile
from service.agent import ChatAgent, get_agent_service
from service.prompt import extrac_user_profile
from utils.auth import get_current_user
from utils import logger
from utils.response import success_response
from models.base import SceneType
from service.scene_manager import _SUMMARY_SCENE_KEYWORDS

from service.database import get_db

class PracticeRequest(BaseModel):
    character: str
    message: str
    session_id: Optional[str] = None


class SummaryRequest(BaseModel):
    session_id: Optional[str] = None
    character: Optional[str] = None


router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/practice")
async def handle_chat_practice(chat_request: PracticeRequest,
                               user: dict = Depends(get_current_user),
                               db: AsyncSession = Depends(get_db),
                               agent: ChatAgent = Depends(get_agent_service)):
    # Create or get session
    character = chat_request.character
    session_id = chat_request.session_id
    user_message = chat_request.message
    learning_stage = user.get("learning_stage", "chinese_chat")

    if learning_stage == "chinese_chat":
        trigger_phrases = ["开始学英语", "开始英文学习", "开始英语学习", "start english", "开始学英文", "开始学习英语"]
        if any(phrase in user_message for phrase in trigger_phrases):
            user.update({"learning_stage": "english_learning"})
            await agent.cache.set(str(user.get("id")), user)
            await agent.conn_manager.send_to_user_channel(user.get("id"),
                                                         "main",
                                                         {
                                                             "action": "ai_message",
                                                             "text": "已经切换到英文学习模式"}
                                                         )

    session_id, ai_text = await agent.generate_chat_flow(db, user, character, user_message, SceneType.NATURAL_PRACTICE,
                                                         session_id=session_id,
                                                         title=character,
                                                         channel="main"
                                                         )

    return success_response(message="ai生成对话成功", data={
                                                            "session_id": session_id,
                                                            "message": ai_text,
                                                        })

def _get_scene_summary_prompt(conversation_text: str) -> str:

    scene_list = [item[0] for item in _SUMMARY_SCENE_KEYWORDS]
    """生成用于识别用户想学习场景的摘要提示，供推荐接口使用。"""
    return f"""根据以下对话，用一句话概括用户想学习的英语场景或主题, 从下面场景列表选择
            {scene_list}。
            若对话中未明确提到场景，可返回空字符串。
            只返回这一句话，不要其他内容。
            
            对话内容：
            {conversation_text}"""


@router.post("/summary")
async def handle_chat_summary(body: SummaryRequest,
                              user: dict = Depends(get_current_user),
                              db: AsyncSession = Depends(get_db),
                              agent: ChatAgent = Depends(get_agent_service)):
    """用户点击学习卡片时调用：若有对话则更新用户 profile 并生成场景摘要供后续推荐使用。"""
    session_id = body.session_id
    character = body.character
    if not session_id or not str(session_id).strip() or not character:
        return success_response(message="没有对话摘要需要保存", data={"summary": ""})

    history_msg = await db_list_chat_messages(db, str(session_id).strip(), character)
    if not history_msg:
        return success_response(message="没有对话摘要需要保存", data={"summary": ""})

    conversation_text = "\n".join([f"{m.role}: {(m.content or '')}" for m in history_msg[-50:]])
    summary_text = ""

    user_prompt = extrac_user_profile(conversation_text)
    system_prompt = "你是一个专业的信息提取助手，只提取对话中明确提到的信息，不进行推断。"
    response = await agent.generate_chat(user_prompt, [], system_prompt)
    json_str = agent.extract_json_from_response(response)
    if json_str:
        new_profile = update_user_profile(user.copy(), json_str)
        if new_profile:
            user.update(new_profile)
            await agent.cache.set(str(user.get("id")), user)
    try:
        scene_prompt = _get_scene_summary_prompt(conversation_text)
        scene_response = await agent.generate_chat(scene_prompt, [], "只返回一句话概括，不要解释。")
        summary_text = scene_response
    except Exception as e:
        logger.warning("summary scene extraction failed: %s", e)

    return success_response(message="对话摘要已经保存", data={
        "message": "我将根据上述对话信息保存您的偏好，并用于推荐学习场景",
        "summary": summary_text,
    })