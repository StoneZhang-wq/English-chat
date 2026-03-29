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
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Optional, Any
import re

from config import configer
from crud.chat import db_create_chat_session, db_add_chat_message, db_list_chat_messages
from models import ChatMessage
from service.agent import ChatAgent, get_agent_service
from utils.auth import get_current_user
from utils import logger
from utils.response import success_response
from models.base import SceneType
from utils.tools import read_file
from service.scene_manager import (
    get_dialogues,
    get_immersive_small_scenes_by_big,
    get_big_scenes_with_immersive,
    get_big_scenes_with_learn,
    build_progress_from_process,
    _derive_npcs_by_small_scene,
    _derive_small_scenes_by_big,
    get_dialogue_by_scene_npc_usage,
)
from service.prompt import (
    get_immersive_chat_system_prompt,
    get_immersive_report_system_prompt,
    get_immersive_report_message,
)
from crud.scene_study import db_get_npc_learn_progress
from service.database import get_db


router = APIRouter(prefix="/api/scene-npc", tags=["scene"])

# ---------- 沉浸式自由对话与报告（复用 dialogue 与 LLM） ----------
class ImmersiveChatRequest(BaseModel):
    """POST /api/scene-npc/immersive-chat 请求体"""
    model_config = ConfigDict(extra="ignore")
    small_scene_id: Optional[str] = ""
    npc_id: Optional[str] = ""
    message: Optional[str] = ""
    history: Optional[List[Dict[str, Any]]] = None
    role_swapped: Optional[bool] = False
    session_id: Optional[str] = ""


class ImmersiveChatReportRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    small_scene_id: Optional[str] = ""
    npc_id: Optional[str] = ""
    transcript: Optional[List[Dict[str, Any]]] = None

@router.get("/big-scenes")
async def handle_get_big_scenes(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent: ChatAgent = Depends(get_agent_service),
):
    """练习模式：返回有 usage=learn 对话的大场景列表（含小场景、角色信息由 small-scenes 等接口补全）。"""
    big_scenes = await get_big_scenes_with_learn(agent, db)
    if not big_scenes:
        dialogues = await get_dialogues(db, agent)
        count = len(dialogues) if isinstance(dialogues, list) else 0
        logger.warning("big-scenes 为空，dialogues_count=%d", count)
        return success_response(message="big-scenes 为空", data={"big_scenes": []})

    return success_response(message="获取big-scenes成功", data={"big_scenes": big_scenes})


async def get_small_scenes_by_big(agent, db, big_scene_id):
    """练习模式自选场景：返回该大场景下、有 learn 对话的小场景列表。"""
    dialogues = await get_dialogues(db, agent)
    if not dialogues:
        return []
    learn_dialogues = [d for d in dialogues if d.get("usage") == "learn"]
    return _derive_small_scenes_by_big(learn_dialogues, big_scene_id)


@router.get("/small-scenes")
async def handle_get_small_scenes(big_scene_id: str,
                                  user: dict = Depends(get_current_user),
                                  db: AsyncSession = Depends(get_db),
                                  agent: ChatAgent = Depends(get_agent_service),
                                 ):
    scenes = await get_small_scenes_by_big(agent, db, big_scene_id)
    return success_response(message="获取small_scenes成功", data={"small_scenes": scenes})


@router.get("/immersive-small-scenes")
async def handle_get_immersive_small_scenes(big_scene_id: str,
                                            user: dict = Depends(get_current_user),
                                            db: AsyncSession = Depends(get_db),
                                            agent: ChatAgent = Depends(get_agent_service),
                                            ):
    """返回某大场景下、有沉浸式内容的小场景列表（含 image URL、can_enter 解锁状态）"""
    user_id = user.get("id") if user else None
    small_scenes = await get_immersive_small_scenes_by_big(agent, db, big_scene_id, user_id=user_id)
    return success_response(message="获取沉浸式小场景成功", data={"small_scenes": small_scenes})


@router.get("/npcs")
async def handle_get_npcs(small_scene_id: str,
                          user: dict = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db),
                          agent: ChatAgent = Depends(get_agent_service),
                          ):
    """返回某小场景下的 NPC 列表，含 id、name、learned、has_content。"""
    user_id = user.get("id")

    dialogues = await get_dialogues(db, agent)
    if not isinstance(dialogues, list):
        dialogues = []

    progress_row = await db_get_npc_learn_progress(db, user_id)
    progress = build_progress_from_process(
        progress_row.process if progress_row else None,
        dialogues,
    )
    by_scene = progress.get("by_scene") or {}
    learned_set = set(by_scene.get(small_scene_id) or [])

    npc_list = _derive_npcs_by_small_scene(dialogues, small_scene_id)
    npcs = [
        {
            "id": n.get("id"),
            "name": n.get("name") or n.get("id"),
            "learned": n.get("id") in learned_set,
            "has_content": True,
        }
        for n in npc_list
    ]
    return success_response(message="获取NPC列表成功", data={"npcs": npcs})


@router.get("/dialogue/learn")
async def handle_get_dialogue_learn(
                                    small_scene_id: str,
                                    npc_id: str,
                                    user: dict = Depends(get_current_user),
                                    db: AsyncSession = Depends(get_db),
                                    agent: ChatAgent = Depends(get_agent_service),
                                ):
    """获取学习对话：GET /api/scene-npc/dialogue/learn?small_scene_id=&npc_id="""
    if not small_scene_id or not npc_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供 small_scene_id 与 npc_id")
    dialogue = await get_dialogue_by_scene_npc_usage(db, agent, small_scene_id, npc_id, "learn")
    if not dialogue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该场景的学习对话")
    return success_response(message="获取学习对话成功", data={"dialogue": dialogue})


@router.get("/dialogue/review")
async def handle_get_dialogue_review(
                                    small_scene_id: str,
                                    npc_id: str,
                                    user: dict = Depends(get_current_user),
                                    db: AsyncSession = Depends(get_db),
                                    agent: ChatAgent = Depends(get_agent_service),
                                ):
    """获取复习对话：GET /api/scene-npc/dialogue/review?small_scene_id=&npc_id="""
    if not small_scene_id or not npc_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供 small_scene_id 与 npc_id")
    dialogue = await get_dialogue_by_scene_npc_usage(db, agent, small_scene_id, npc_id, "review")
    if not dialogue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该场景的复习对话")
    return success_response(message="获取复习对话成功", data={"dialogue": dialogue})


def _first_speaker_is_a(content: List[Dict]) -> bool:
    """根据原 immersive 对话 content 判断是否 A 角色先发言。"""
    if not content or not isinstance(content, list):
        return False
    first = content[0] if isinstance(content[0], dict) else None
    if not first:
        return False
    role = (first.get("role") or "A").strip().upper()
    return role == "A"


@router.get("/dialogue/immersive")
async def handle_get_dialogue_immersive(
                                        small_scene_id: str,
                                        npc_id: str,
                                        user: dict = Depends(get_current_user),
                                        db: AsyncSession = Depends(get_db),
                                        agent: ChatAgent = Depends(get_agent_service),
                                    ):
    """获取沉浸式对话：创建新 ChatSession；若原对话中 A 先发言则预生成 AI 首句及音频并写入 session，返回 dialogue、session_id、first_ai_text、first_ai_audio_url。"""
    if not small_scene_id or not npc_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供 small_scene_id 与 npc_id")
    dialogue = await get_dialogue_by_scene_npc_usage(db, agent, small_scene_id, npc_id, "immersive")
    if not dialogue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该场景的沉浸式对话")
    npc_name = (dialogue.get("npc_name") or dialogue.get("npc_id") or npc_id).strip() or npc_id
    session = await db_create_chat_session(db, user.get("id"), int(SceneType.AI_CHAT.value), npc_name)
    session_id = session.id

    first_ai_text = ""
    first_ai_audio_url = None
    content = dialogue.get("content") or []
    if _first_speaker_is_a(content):
        first_item = content[0] if isinstance(content[0], dict) else {}
        first_ai_text = (first_item.get("content") or first_item.get("text") or "").strip()
        if first_ai_text:
            user_id = user.get("id")
            tts_dir = os.path.join(configer.data_path, "audio", "tts", str(user_id))
            try:
                os.makedirs(tts_dir, exist_ok=True)
            except Exception as e:
                logger.warning("创建 TTS 目录失败（首句）: %s", e)
            else:
                filename = f"main_immersive_first_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000)}.wav"
                output_path = os.path.join(tts_dir, filename)
                success = await agent.doubao_service.generate_speech(
                    first_ai_text, output_path, user_id, "main",
                    voice_type=getattr(configer, "tts_voice_type", None),
                    conn_manager=agent.conn_manager,
                )
                if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    first_ai_audio_url = f"/api/audio/tts/{filename}"
            await db_add_chat_message(db, session_id, "assistant", first_ai_text, npc_name)

    data = {"dialogue": dialogue, "session_id": session_id}
    if first_ai_text:
        data["first_ai_text"] = first_ai_text
    if first_ai_audio_url:
        data["first_ai_audio_url"] = first_ai_audio_url
    return success_response(message="获取沉浸式对话成功", data=data)


def _content_to_reference_script(content: List[Dict]) -> str:
    """将 dialogue content 列表格式化为 A: / B: 参考剧本字符串。"""
    if not content or not isinstance(content, list):
        return ""
    lines = []
    for item in content:
        if not isinstance(item, dict):
            continue
        role = (item.get("role") or "A")[:1].upper()
        text = item.get("content") or item.get("text") or ""
        if text:
            lines.append(f"{role}: {text.strip()}")
    return "\n".join(lines)


@router.post("/immersive-chat")
async def handle_immersive_chat(
    req: ImmersiveChatRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent: ChatAgent = Depends(get_agent_service),
):
    """沉浸式自由对话：历史从该 session 读取并作为 LLM 上下文；系统提示含完整 immersive 剧本；AI 语音存 ./data/audio/tts/{user_id}，与用户练习模式一致。"""
    small_scene_id = req.small_scene_id
    npc_id = req.npc_id
    message = (req.message or "").strip()
    if not small_scene_id or not npc_id or not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供 small_scene_id、npc_id 与 message")

    dialogue = await get_dialogue_by_scene_npc_usage(db, agent, small_scene_id, npc_id, "immersive")
    if not dialogue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="获取沉浸式体验场景对话失败")

    npc_name = (dialogue.get("npc_name") or dialogue.get("npc_id") or npc_id) if dialogue else npc_id
    user_goal = (dialogue.get("user_goal") or "").strip() if dialogue else ""
    reference_script = _content_to_reference_script(dialogue.get("content") or []) if dialogue else ""

    session_id = (req.session_id or "").strip()
    if not session_id:
        session = await db_create_chat_session(db, user.get("id"), int(SceneType.AI_CHAT.value), npc_name)
        session_id = session.id

    history_msg = await db_list_chat_messages(db, session_id, character=npc_name)
    system_prompt = get_immersive_chat_system_prompt(
        npc_name=npc_name,
        user_goal=user_goal,
        role_swapped=req.role_swapped is True,
        reference_script=reference_script,
    )
    response = await agent.generate_chat(message, history_msg, system_prompt, msg_limit=20)
    reply = ""
    hints: List[str] = []
    if isinstance(response, str):
        # 优先从回复中提取 JSON（允许存在代码块等包装）
        json_str = agent.extract_json_from_response(response)
        if json_str:
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    reply = (parsed.get("reply") or "").strip()
                    raw_hints = parsed.get("hints") or []
                    if isinstance(raw_hints, list):
                        hints = [str(h).strip() for h in raw_hints if str(h).strip()]
            except json.JSONDecodeError:
                pass
        # 若未成功解析 JSON，则尝试解析 "reply: ..., hints: ..." 这种兜底格式
        if not reply:
            text = response.strip()
            m_reply = re.search(r"reply\s*:\s*(.+?)(?:,\s*hints\s*:|$)", text, re.IGNORECASE)
            if m_reply:
                reply = m_reply.group(1).strip()
            m_hints = re.search(r"hints\s*:\s*(.+)$", text, re.IGNORECASE)
            if m_hints:
                raw = m_hints.group(1).strip()
                parts = [p.strip() for p in re.split(r"\s*,\s*", raw) if p.strip()]
                hints = parts
        # 如果仍未解析出 reply，则退回整段文本
        if not reply:
            reply = response.strip()
    else:
        reply = str(response).strip()

    audio_url = None
    user_id = user.get("id")
    tts_dir = os.path.join(configer.data_path, "audio", "tts", str(user_id))
    try:
        os.makedirs(tts_dir, exist_ok=True)
    except Exception as e:
        logger.warning("创建 TTS 目录失败: %s", e)
    else:
        filename = f"main_immersive_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000)}.wav"
        output_path = os.path.join(tts_dir, filename)
        success = await agent.doubao_service.generate_speech(
            reply, output_path, user_id, "main",
            voice_type=getattr(configer, "tts_voice_type", None),
            conn_manager=agent.conn_manager,
        )
        if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            audio_url = f"/api/audio/tts/{filename}"

    await db_add_chat_message(db, session_id, "user", message, npc_name)
    await db_add_chat_message(db, session_id, "assistant", reply, npc_name)

    return success_response(message="回复成功", data={
        "status": "success",
        "session_id": session_id,
        "reply": reply,
        "hints": hints,
        "task_completed": False,
        "audio_url": audio_url,
    })


@router.post("/immersive-chat/report")
async def handle_immersive_chat_report(
    req: ImmersiveChatReportRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent: ChatAgent = Depends(get_agent_service),
):
    """生成沉浸式对话总结报告：含「对话是否偏离主题」「句型/语法/发音」「下一步建议」，返回 report_markdown、reference_script、core_sentences、core_chunks。"""
    small_scene_id = (req.small_scene_id or "").strip()
    npc_id = (req.npc_id or "").strip()
    transcript = req.transcript if isinstance(req.transcript, list) else []
    if not small_scene_id or not npc_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供 small_scene_id 与 npc_id")

    reference_script = ""
    core_sentences = ""
    core_chunks = ""
    dialogue_topic = ""

    d_review = await get_dialogue_by_scene_npc_usage(db, agent, small_scene_id, npc_id, "review")
    if d_review:
        reference_script = _content_to_reference_script(d_review.get("content") or [])
        core_sentences = (d_review.get("core_sentences") or "").strip()
        core_chunks = (d_review.get("core_chunks") or "").strip()

    d_immersive = await get_dialogue_by_scene_npc_usage(db, agent, small_scene_id, npc_id, "immersive")
    if d_immersive:
        dialogue_topic = (d_immersive.get("user_goal") or "").strip() or (d_immersive.get("user_goal_a") or "").strip()
    if not dialogue_topic and reference_script:
        dialogue_topic = "（以参考剧本为准）"

    report_markdown = ""
    if transcript:
        try:
            user_message = get_immersive_report_message(
                transcript, reference_script=reference_script, dialogue_topic=dialogue_topic
            )
            system_prompt = get_immersive_report_system_prompt()
            response = await agent.generate_chat(user_message, [], system_prompt=system_prompt)
            report_markdown = (agent.sanitize_response(response) or "").strip()
        except Exception as e:
            logger.warning("immersive-chat/report LLM 失败: %s", str(e))
            report_markdown = "生成报告时出错，请稍后重试。"

    return success_response(
        message="报告生成成功",
        data={
            "status": "success",
            "report_markdown": report_markdown,
            "reference_script": reference_script,
            "core_sentences": core_sentences,
            "core_chunks": core_chunks,
        },
    )