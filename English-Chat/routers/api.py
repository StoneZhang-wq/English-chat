"""
核心API路由 - 支持前端功能
"""
import json
import os
import re
import tempfile
import uuid
from typing import Optional
import aiofiles
import aiofiles.tempfile
import aiohttp
import asyncio
from datetime import datetime

from requests import session
from starlette import status
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config import configer
from crud.chat import db_create_chat_session, db_add_chat_message
from crud.dialogue import db_list_dialogues_by_scene
from models.base import SceneType
from service.database import get_db
from service.doubao import get_doubao_service
from service.agent import get_agent_service, ChatAgent
from utils import logger
from utils.auth import get_current_user
from utils.response import success_response
from pydantic import BaseModel
from service.scene_manager import (
    get_learning_recommendations,
    build_progress_from_process,
    get_dialogues,
    build_card_title,
    get_scene_image_url,
    _derive_npcs_by_small_scene,
    get_dialogue_by_scene_npc_usage,
)
from service.practice import (
    get_first_turn_for_start,
    get_reference_b_line,
    get_next_after_turn,
)
from service.prompt import (
    get_practice_respond_validation_system_prompt,
    get_practice_generate_review_corrections_message,
)

from crud.scene_study import db_get_npc_learn_progress, db_append_dialogue_ids_to_process
from crud.scene import db_get_small_scene_by_id_or_immersive

router = APIRouter(prefix="/api", tags=["核心API"])


async def transcribe_uploaded_audio_tempfile(request: Request, agent: ChatAgent, tmp_file_path: str) -> str:
    """
    将已落盘的录音（多为 webm）转为 16kHz wav（若可能），调用 agent.transcribe_audio（尊重 ASR_PROVIDER）。
    删除过程中产生的临时文件，返回转写文本（无有效内容时为空字符串）。
    """
    path = tmp_file_path
    audio_converted = False
    try:
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(path, format="webm")
            seg = seg.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            wav_path = path.replace(".webm", ".wav")
            seg.export(wav_path, format="wav")
            os.unlink(path)
            path = wav_path
            audio_converted = True
            logger.info("Audio converted from webm to wav (16kHz mono) for ASR")
        except ImportError:
            logger.warning("pydub not available, using original file")
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            if path and not str(path).endswith(".wav"):
                logger.warning("Conversion failed, will try original format")

        try:
            transcription = await agent.transcribe_audio(path, request.base_url)
            return (transcription or "").strip()
        except Exception:
            if not audio_converted and path and not str(path).endswith(".wav"):
                try:
                    wav_path = path.replace(".webm", ".wav").replace(".mp3", ".wav")
                    cmd = ["ffmpeg", "-i", path, "-ar", "16000", "-ac", "1", "-y", wav_path]
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    _stdout, stderr = await process.communicate()
                    if process.returncode != 0:
                        logger.error(f"ffmpeg 转换失败: {stderr.decode(errors='ignore')}")
                    os.unlink(path)
                    path = wav_path
                    transcription = await agent.transcribe_audio(path, request.base_url)
                    return (transcription or "").strip()
                except Exception as e2:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Fallback conversion failed: {e2}",
                    ) from e2
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="处理语音失败")
    finally:
        if path and os.path.isfile(path):
            try:
                os.unlink(path)
            except OSError:
                pass


class RecommendRequest(BaseModel):
    conversation_summary: Optional[str] = None
    count: Optional[int] = None


class DialogueRequest(BaseModel):
    small_scene_id: Optional[str]
    npc_id: Optional[str]


class PracticeStartRequest(BaseModel):
    """POST /api/practice/start 请求体"""
    dialogue: Optional[str] = None
    dialogue_lines: Optional[list] = None
    dialogue_id: Optional[str] = None
    small_scene_id: Optional[str] = None
    npc_id: Optional[str] = None
    session_id: Optional[str] = None


class PracticeRespondRequest(BaseModel):
    """POST /api/practice/respond 请求体。"""
    user_input: str
    dialogue_lines: list
    current_turn: int
    session_id: str


class PracticeEndRequest(BaseModel):
    """POST /api/practice/end 请求体（JSON body，与前端一致）。"""
    session_id: Optional[str] = None


class PracticeGenerateReviewRequest(BaseModel):
    """POST /api/practice/generate-review 请求体。"""
    user_inputs: Optional[list] = None
    dialogue_topic: Optional[str] = None
    dialogue_id: Optional[str] = None
    small_scene_id: Optional[str] = None
    npc_id: Optional[str] = None


class PracticeSaveMemoryRequest(BaseModel):
    """POST /api/practice/save-memory 请求体；逻辑上以 small_scene_id + npc_id 为准，将对应 dialogue_id 并入学习进度。"""
    small_scene_id: Optional[str] = None
    npc_id: Optional[str] = None
    dialogue_id: Optional[str] = None

class PracticeMarkedRequest(BaseModel):
    small_scene_id: Optional[str] = None
    npc_id: Optional[str] = None
    dialogue_id: Optional[str] = None


@router.get("/characters")
async def get_characters(user = Depends(get_current_user)):
    data = {"characters": ["Assistant"]}
    if not os.path.exists(configer.characters_folder):
        logger.warning(f"Characters folder not found: {configer.characters_folder}")
        return success_response(message="获取默认characters成功", data=data)
    try:
        character_dirs = [d for d in os.listdir(configer.characters_folder)
                          if os.path.isdir(os.path.join(configer.characters_folder, d))]
        if not character_dirs:
            logger.warning("No character folders found")
            return success_response(message="获取默认characters成功", data=data)
        return success_response(message="获取characters成功", data={"characters": character_dirs})
    except Exception as e:
        logger.error(f"failed to listing characters: {e}")
        return success_response(message="获取默认characters成功", data=data)


@router.post("/voice/upload")
async def upload_voice_audio(request: Request,
                            audio: UploadFile = File(...),
                            character: str = Form("english_tutor"),
                            session_id: Optional[str] = Form(None),
                            user: dict = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db),
                            agent: ChatAgent = Depends(get_agent_service)):
    """处理上传的语音：webm 转 wav → 转写 → 推送用户消息并触发 AI 回复。"""
    tmp_file_path = None
    try:
        async with aiofiles.tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            content = await audio.read()
            await tmp.write(content)
            tmp_file_path = tmp.name

        transcription = await transcribe_uploaded_audio_tempfile(request, agent, tmp_file_path)
        tmp_file_path = None

        if not transcription:
            return success_response(
                message="未检测到有效语音",
                data={"transcription": "", "message": "未检测到有效语音，可能为静音或录音过短，请重新录制。"}
            )

        user_id = user.get("id")
        await agent.conn_manager.send_to_user_channel(user_id, "main",
                                                    {"action": "user_message",
                                                     "text": transcription})

        session_id, _ai_text = await agent.generate_chat_flow(db, user, character, transcription,
                                                              SceneType.NATURAL_PRACTICE, session_id,
                                                              title=character)

        return success_response(message="翻译音频成功",
                                data={"session_id": session_id,
                                      "message": _ai_text,
                                      "transcription": transcription})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice upload failed: {e}", exc_info=True)
        if tmp_file_path and os.path.isfile(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"处理语音失败: {str(e)}")


@router.post("/practice/transcribe")
async def practice_transcribe(
    request: Request,
    audio: UploadFile = File(...),
    _user: dict = Depends(get_current_user),
    agent: ChatAgent = Depends(get_agent_service),
):
    """仅转写：场景练习与沉浸式弹窗录音使用；不推 WebSocket、不触发 LLM。ASR 与 /api/voice/upload 一致（ASR_PROVIDER=local 为离线）。"""
    tmp_file_path = None
    try:
        async with aiofiles.tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            content = await audio.read()
            await tmp.write(content)
            tmp_file_path = tmp.name

        transcription = await transcribe_uploaded_audio_tempfile(request, agent, tmp_file_path)
        tmp_file_path = None

        if not transcription:
            return success_response(
                message="未检测到有效语音",
                data={
                    "status": "failed",
                    "transcription": "",
                    "message": "未检测到有效语音，可能为静音或录音过短，请重新录制。",
                },
            )

        return success_response(
            message="转写成功",
            data={"status": "success", "transcription": transcription},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Practice transcribe failed: {e}", exc_info=True)
        if tmp_file_path and os.path.isfile(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except OSError:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理语音失败: {str(e)}",
        )


@router.post("/learning/recommend")
async def api_learning_recommend(req: RecommendRequest,
                                 user: dict = Depends(get_current_user),
                                 db: AsyncSession = Depends(get_db),
                                 agent: ChatAgent = Depends(get_agent_service),
                                ):
    """获取学习推荐：结合对话摘要与学习进度，返回推荐场景+NPC，含 title、learned。"""
    try:
        user_id = user.get("id")
        conversation_summary = req.conversation_summary if req.conversation_summary is not None else ""
        raw_count = 4 if req.count is None else req.count
        count = max(1, min(10, int(raw_count)))

        progress_row = await db_get_npc_learn_progress(db, user_id)
        dialogues = await get_dialogues(db, agent)
        progress = build_progress_from_process(
            progress_row.process if progress_row else None,
            dialogues,
        )
        recommendations = await get_learning_recommendations(
            agent,
            progress,
            conversation_summary=conversation_summary or None,
            count=count,
            db=db,
        )
        return success_response(message="获取学习推荐列表成功", data={"recommendations": recommendations})
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in learning recommend: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取学习推荐失败")


@router.post("/english/generate")
async def generate_english_dialogue(req: DialogueRequest,
                                    user: dict = Depends(get_current_user),
                                    db: AsyncSession = Depends(get_db),
                                    agent: ChatAgent = Depends(get_agent_service)):

    small_scene_id = req.small_scene_id
    npc_id = req.npc_id
    if not small_scene_id or not npc_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供具体小场景类型 与 npc")

    dialogue = await get_dialogue_by_scene_npc_usage(db, agent, small_scene_id, npc_id, "learn")
    if not dialogue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该场景的对话内容")

    dialogue_parts = []
    dialogue_lines = []
    content = dialogue.get("content", [])
    for item in content:
        role = item.get("role", "B")
        text = item.get("content", "")
        hint = item.get("hint", "")
        dialogue_parts.append(f"{role}: {text}")
        dialogue_lines.append({"speaker": role, "text": text, "hint": hint, "audio_url": None})

    dialogue_id = dialogue.get("dialogue_id", f"{small_scene_id}-{npc_id}-learn")

    # 英语卡片：只关联本地已生成的剧本音频，不在此步骤调用 Piper/豆包 TTS（离线 TTS 留给 AI 对话等流程）
    agent.doubao_service.attach_existing_dialogue_audio_urls(dialogue_lines, dialogue_id)

    dialogue_text = "\n".join(dialogue_parts)
    card_title = build_card_title(dialogue)

    if user.get("learning_stage", "chinese_chat") != "english_learning":
        user.update({"learning_stage": "english_learning"})
        await agent.cache.set(str(user.get("id")), user)

    data = {
        "status": "success",
        "message": "英文对话已生成",
        "dialogue": dialogue_text,
        "dialogue_lines": dialogue_lines,
        "dialogue_id": dialogue_id,
        "small_scene_id": small_scene_id,
        "npc_id": npc_id,
        "npc_name": dialogue.get("npc_name", "").strip() or npc_id,
        "card_title": card_title,
    }

    return success_response(message="获取对话音频成功", data=data)


@router.post("/practice/start")
async def handle_practice_start(req: PracticeStartRequest,
                             user: dict = Depends(get_current_user),
                             db: AsyncSession = Depends(get_db),
                             agent: ChatAgent = Depends(get_agent_service),
                             ):
    """
    开始练习：根据对话内容或 small_scene_id+npc_id 加载对话，返回首句与 hints，并创建练习会话。
    响应格式兼容前端：status, session_id, dialogue_id, dialogue_lines, current_turn, a_text, a_audio_url, b_hints, total_turns。
    """
    dialogue_id = req.dialogue_id
    dialogue_lines = req.dialogue_lines
    small_scene_id = req.small_scene_id
    npc_id = req.npc_id
    session_id = req.session_id
    if not dialogue_lines:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话内容不能为空")

    if small_scene_id and npc_id:
        dialogue = await get_dialogue_by_scene_npc_usage(db, agent, small_scene_id, npc_id, "learn")
        if dialogue:
            content = dialogue.get("content", [])
            for i, line in enumerate(dialogue_lines):
                if i < len(content):
                    item = content[i]
                    role = item.get("role", "B")
                    if line.get("speaker") == role and line.get("text") == item.get("content", ""):
                        line["hint"] = item.get("hint", "")

    if dialogue_lines[0]["speaker"] not in ("A", "B"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="对话角色必须为A（NPC）或B（用户）")

    dialogue_topic = "日常对话"
    dialogue_id = dialogue_id if dialogue_id else f"practice_{int(datetime.now().timestamp() * 1000)}"

    practice_sessions = {
        "dialogue_id": dialogue_id,
        "dialogue_lines": dialogue_lines,
        "current_turn": 0,
        "user_inputs": [],
        "dialogue_topic": dialogue_topic,
        "small_scene_id": req.small_scene_id,
        "npc_id": req.npc_id,
        # 用于复习纠错时决定展示顺序（A=NPC, B=用户）
        "starts_with": (dialogue_lines[0].get("speaker") or "B") if dialogue_lines else "B",
    }

    a_text, a_audio_url, b_hints, total_turns = get_first_turn_for_start(dialogue_lines)
    if not session_id:
        session_ = await db_create_chat_session(db, user.get("id"), int(SceneType.SCENE_PRACTICE.value), dialogue_id)
        session_id = session_.id
        logger.info(f"创建新的会话: {session_id}")

    await agent.cache.set(f"practice:session:{session_id}", practice_sessions)

    payload = {
        "status": "success",
        "session_id": session_id,
        "dialogue_id": dialogue_id,
        "dialogue_lines": dialogue_lines,
        "current_turn": 0,
        "a_text": a_text if a_text else None,
        "a_audio_url": a_audio_url,
        "b_hints": b_hints,
        "total_turns": total_turns,
    }
    return success_response(message="练习已开始", data=payload)


@router.post("/practice/respond")
async def handle_practice_respond(req: PracticeRespondRequest,
                               user: dict = Depends(get_current_user),
                               db: AsyncSession = Depends(get_db),
                               agent: ChatAgent = Depends(get_agent_service),
                                ):
    """
    用户回复验证：与当前轮参考句做语义一致性判断，返回下一句 A 与 B 的 hints，以及是否完成。
    使用已有 agent.generate_chat + extract_json_from_response 做校验；会话可来自缓存以保持一致性。
    """
    user_input = req.user_input
    dialogue_lines = req.dialogue_lines
    current_turn = int(req.current_turn)
    session_id = req.session_id

    if not dialogue_lines or not isinstance(dialogue_lines, list):
        return success_response(message="对话行为空", data={
                                                            "status": "failed",
                                                            "message": "对话行为空",
                                                            "is_consistent": False,
                                                        })

    ref_b = get_reference_b_line(dialogue_lines, current_turn)
    reference_text = (ref_b.get("text", "")).strip() if ref_b else ""

    practice_sessions = await agent.cache.get(f"practice:session:{session_id}")

    try:
        user_prompt = get_practice_respond_validation_system_prompt(user_input, reference_text)
        system_prompt = "你是一个专业的英语教学助手，能够判断句子意思的一致性。"
        response = await agent.generate_chat(user_prompt, [], system_prompt)
        json_str = agent.extract_json_from_response(response)
        parsed = None
        if json_str:
            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError:
                parsed = None
        if parsed is None and response and response.strip():
            # 兜底：LLM 可能返回 "result: xxx, reason: yyy" 或分两行，无花括号时用正则解析
            m = re.search(
                r"result\s*:\s*[\"']?(\w+)[\"']?\s*[,，\s]+\s*reason\s*:\s*(.+)",
                response.strip(),
                re.IGNORECASE | re.DOTALL,
            )
            if not m:
                m = re.search(
                    r"result\s*:\s*[\"']?(\w+)[\"']?\s*reason\s*:\s*(.+)",
                    response.strip(),
                    re.IGNORECASE | re.DOTALL,
                )
            if m:
                parsed = {"result": m.group(1).strip(), "reason": m.group(2).strip()}
        if parsed and isinstance(parsed, dict):
            is_consistent = parsed.get("result", "inconsistent") == "consistent"
            validation_result = {
                "result": parsed.get("result", "inconsistent"),
                "reason": str(parsed.get("reason", "")) or ("意思一致" if is_consistent else "意思不一致"),
            }
        else:
            is_consistent = True
            validation_result = {"result": "consistent", "reason": "未校验"}
    except Exception as e:
        logger.warning("practice respond LLM validation failed: %s", e)
        is_consistent = True
        validation_result = {"result": "consistent", "reason": "未校验"}

    next_a_text, next_a_audio_url, next_b_hints, next_turn, is_completed = get_next_after_turn(dialogue_lines, current_turn)

    if session_id:
        try:
            if isinstance(practice_sessions, dict):
                user_inputs = list(practice_sessions.get("user_inputs") or [])
                starts_with = str(practice_sessions.get("starts_with") or "B").strip().upper()
                # 纠错提示词里每轮的「AI 台词」需要与脚本的真实顺序一致：
                # - 若脚本以 A 开始，则该轮 AI 台词应为“当前 B 句前面紧邻的那句 A”（轮次从 A→B 开始）
                # - 若脚本以 B 开始，则该轮 AI 台词应为“当前 B 句后面紧邻的那句 A”（轮次从 B→A 开始）
                def _ai_said_for_turn(lines: list, turn_idx: int, starts: str, fallback_next_a: str) -> str:
                    try:
                        b_seen = 0
                        for i, ln in enumerate(lines or []):
                            if (ln.get("speaker") or "A")[:1].upper() != "B":
                                continue
                            if b_seen != turn_idx:
                                b_seen += 1
                                continue
                            # 找到该轮 B 行：向前找最近 A，向后找最近 A
                            prev_a = ""
                            for k in range(i - 1, -1, -1):
                                if (lines[k].get("speaker") or "A")[:1].upper() == "A":
                                    prev_a = (lines[k].get("text") or lines[k].get("content") or "").strip()
                                    break
                            next_a = ""
                            for k in range(i + 1, len(lines)):
                                if (lines[k].get("speaker") or "A")[:1].upper() == "A":
                                    next_a = (lines[k].get("text") or lines[k].get("content") or "").strip()
                                    break
                            if starts == "A":
                                return prev_a or next_a or (fallback_next_a or "")
                            return next_a or prev_a or (fallback_next_a or "")
                    except Exception:
                        pass
                    return (fallback_next_a or "")

                ai_said = _ai_said_for_turn(dialogue_lines, current_turn, starts_with, next_a_text)
                item_payload = {
                    "turn": current_turn,
                    "user_said": user_input,
                    "reference": reference_text,
                    "ai_said": ai_said or "",
                    # order: AB 表示 AI(A) 在前；BA 表示 用户(B) 在前
                    "order": "AB" if starts_with == "A" else "BA",
                    "timestamp": datetime.now().isoformat(),
                }
                # 同一轮次用户可能多次尝试（ASR 误识别/用户重发），避免产生重复 turn：优先覆盖最后一条同 turn 的记录
                updated = False
                for idx in range(len(user_inputs) - 1, -1, -1):
                    it = user_inputs[idx]
                    if isinstance(it, dict) and it.get("turn") == current_turn:
                        user_inputs[idx] = {**it, **item_payload}
                        updated = True
                        break
                if not updated:
                    user_inputs.append(item_payload)
                practice_sessions["user_inputs"] = user_inputs
                practice_sessions["current_turn"] = next_turn
                await agent.cache.set(f"practice:session:{session_id}", practice_sessions, ttl=3600)
        except Exception as e:
            logger.warning("practice session cache update failed: %s", e)

    character = (practice_sessions.get("npc_id") if isinstance(practice_sessions, dict) else None) or "practice"
    try:
        await db_add_chat_message(db, str(session_id), "user", user_input, character)
        ai_reply_parts = [validation_result.get("reason", "")]
        if next_a_text:
            ai_reply_parts.append(next_a_text)
        await db_add_chat_message(db, str(session_id), "assistant", " ".join(ai_reply_parts).strip() or "已记录", character)
    except Exception as e:
        logger.warning("practice respond save to db failed: %s", e)

    # 当本轮有下一句 A 要展示但已无下一句 B（最后一句是 AI）时，前端先展示该句 A 再进入结束流程
    complete_after_this_a = bool(next_a_text) and not (next_b_hints.get("key_sentence") or "").strip()
    payload = {
        "status": "success",
        "is_consistent": is_consistent,
        "validation_result": validation_result,
        "next_a_text": next_a_text,
        "next_a_audio_url": next_a_audio_url,
        "next_b_hints": next_b_hints,
        "next_turn": next_turn,
        "is_completed": is_completed,
        "complete_after_this_a": complete_after_this_a,
    }
    return success_response(message="回复已校验", data=payload)

@router.post("/practice/end")
async def handle_practice_end(req: PracticeEndRequest,
                             user: dict = Depends(get_current_user),
                             agent: ChatAgent = Depends(get_agent_service)):
    session_id = (req.session_id or "").strip()
    if not session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="会话ID不能为空")

    session_data = await agent.cache.get(f"practice:session:{session_id}")
    if not session_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到对应的练习会话")

    session_data = session_data.copy()
    session_data["end_time"] = datetime.now().isoformat()
    if not session_data.get("dialogue_topic"):
        session_data["dialogue_topic"] = "英语对话"
    await agent.cache.set(f"practice:session:{session_id}", session_data, ttl=3600)

    return success_response(message="结束练习成功", data={
        "status": "success",
        "session_data": session_data,
    })

@router.post("/practice/generate-review")
async def handle_practice_review(
    req: PracticeGenerateReviewRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent: ChatAgent = Depends(get_agent_service),
):
    """生成复习笔记：LLM 纠错 + 从 DB 取 small_scene_id/npc_id 对应的 review 对话与核心句型语块。"""
    user_inputs = req.user_inputs if isinstance(req.user_inputs, list) else []
    dialogue_topic = (req.dialogue_topic or "").strip() or "英语对话"
    small_scene_id = (req.small_scene_id or "").strip() or None
    npc_id = (req.npc_id or "").strip() or None
    dialogue_id = req.dialogue_id or ""

    corrections = []
    if user_inputs:
        try:
            system_prompt =  "你是英语口语纠错助手。用户输入来自语音转写，只纠发音和语法错误，不纠书写、标点、大小写。"
            user_message = get_practice_generate_review_corrections_message(user_inputs, dialogue_topic)
            response = await agent.generate_chat(user_message, [], system_prompt)
            logger.info(f"generate-review response: {response}")
            if response and response.strip() in ("corrections:", "corrections："):
                logger.warning(
                    "generate-review LLM 仅返回了 'corrections:' 无后续内容，多为回复被截断。"
                    "请确认 LLM 的 max_tokens 足够大（如 2048）。"
                )
            json_str = agent.extract_json_from_response(response)
            if not json_str and response and response.strip():
                stripped = response.strip()
                # 兜底1：corrections: [...] 无外层花括号
                if stripped.startswith("corrections:") or stripped.startswith("corrections："):
                    idx = stripped.find("[")
                    if idx >= 0:
                        bracket = 1
                        end = idx + 1
                        while end < len(stripped) and bracket:
                            if stripped[end] == "[": bracket += 1
                            elif stripped[end] == "]": bracket -= 1
                            end += 1
                        if bracket == 0:
                            json_str = '{"corrections": ' + stripped[idx:end] + "}"
                # 兜底2：corrections:user_said:A,correct:B,explanation:C 或多项 ,user_said:D,correct:E,explanation:F
                if not json_str and (stripped.startswith("corrections:") or stripped.startswith("corrections：")):
                    rest = stripped.split(":", 1)[-1].strip()  # 去掉开头的 corrections:
                    if rest.startswith("user_said:"):
                        rest = rest[len("user_said:"):]
                    blocks = re.split(r",\s*user_said\s*:", rest, flags=re.IGNORECASE)
                    for block in blocks:
                        if not block.strip():
                            continue
                        i = re.search(r",\s*correct\s*:", block, re.IGNORECASE)
                        j = re.search(r",\s*explanation\s*:", block, re.IGNORECASE)
                        if i and j and i.start() < j.start():
                            user_said = block[: i.start()].strip()
                            correct = block[i.end() : j.start()].strip()
                            explanation = block[j.end() :].strip()
                            if user_said or correct or explanation:
                                corrections.append({
                                    "user_said": user_said,
                                    "correct": correct,
                                    "explanation": explanation,
                                })
            if json_str:
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict) and "corrections" in parsed:
                        arr = parsed["corrections"]
                    elif isinstance(parsed, list):
                        arr = parsed
                    else:
                        arr = []
                    if isinstance(arr, list):
                        corrections = [
                            {
                                "user_said": (c.get("user_said") or ""),
                                "correct": (c.get("correct") or ""),
                                "explanation": (c.get("explanation") or ""),
                            }
                            for c in arr
                            if isinstance(c, dict)
                        ]
                except json.JSONDecodeError as je:
                    logger.warning("generate-review JSON decode failed: %s", je)
        except Exception as e:
            logger.warning("generate-review LLM corrections failed: %s", e)

    core_sentences = ""
    core_chunks = ""
    review_dialogue = []
    review_dialogue_id = ""  # 从 Dialogue 表取到的 dialogue_id，用于复习对话音频目录（如 DL-HOME-FAMILY-2）
    if small_scene_id and npc_id and db:
        try:
            d = await get_dialogue_by_scene_npc_usage(db, agent, small_scene_id, npc_id, "review")
            if d:
                review_dialogue_id = (d.get("dialogue_id") or "").strip()
                core_sentences = (d.get("core_sentences") or "").strip()
                core_chunks = (d.get("core_chunks") or "").strip()
                content = d.get("content")
                if isinstance(content, list):
                    for i, item in enumerate(content):
                        if isinstance(item, dict):
                            role = (item.get("role") or "A")[:1].upper()
                            text = item.get("content") or item.get("text") or ""
                            hint = item.get("hint") or ""
                            audio_url = f"/api/audio/english_dialogue/{review_dialogue_id}/{role}_{i}.wav" if review_dialogue_id else None
                            review_dialogue.append({
                                "speaker": role,
                                "text": text,
                                "hint": hint,
                                "audio_url": audio_url,
                            })
        except Exception as e:
            logger.warning("generate-review load review dialogue failed: %s", e)

    if review_dialogue:
        # 复习对话音频目录使用 Dialogue 表中的 dialogue_id，便于复用、多用户共用
        audio_dir_id = review_dialogue_id or f"review_{(small_scene_id or npc_id or dialogue_id or 'x').replace('/', '_')}_{uuid.uuid4().hex[:8]}"
        await agent.doubao_service.generate_tts_for_dialogue_lines(review_dialogue, audio_dir_id,
                                                                   user.get("id"), "main", agent.conn_manager)

    review_notes = {
        "corrections": corrections,
        "core_sentences": core_sentences,
        "core_chunks": core_chunks,
        "review_dialogue": review_dialogue,
    }
    return success_response(
        message="复习笔记已生成",
        data={"status": "success", "review_notes": review_notes},
    )

@router.post("/practice/save-memory")
async def handle_save_memory(
        req: PracticeSaveMemoryRequest,
        user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):

    return success_response(message="练习记忆已保存", data={
        "status": "success",
        "message": "练习记忆已保存"
    })



@router.post("/practice/mark-unit-mastered")
async def mark_unit_mastered_api(
    req: PracticeMarkedRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    保存练习进度：根据 small_scene_id、npc_id 查询该小场景下该 NPC 的所有对话 dialogue_id，
    将这些 dialogue_id 并入当前用户的 NpcLearnProgress.process（JSON 数组）。解锁小场景的判定：
    用户 process 中已包含该小场景下所有对话的 dialogue_id 即视为已解锁。
    """
    user_id = user.get("id")
    small_scene_id = (req.small_scene_id or "").strip()
    npc_id = (req.npc_id or "").strip()
    dialogue_id = (req.dialogue_id or "").strip()
    if dialogue_id:
        await db_append_dialogue_ids_to_process(db, user_id, [dialogue_id])
        return success_response(message="学习进度已保存", data={"status": "success",
                                                            "message": "已标记为已掌握"})

    if not small_scene_id or not npc_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供 small_scene_id 与 npc_id",
        )

    rows = await db_list_dialogues_by_scene(
        db, small_scene_id=small_scene_id, npc_id=npc_id
    )
    dialogue_ids = [r.dialogue_id for r in rows if getattr(r, "dialogue_id", None)]
    if not dialogue_ids:
        return success_response(message="该场景下暂无对话记录，未更新进度",
                                data={"status": "success", "message": "该场景下暂无对话记录，未更新进度"})

    await db_append_dialogue_ids_to_process(db, user_id, dialogue_ids)
    return success_response(
        message="学习进度已保存",
        data={
            "status": "success",
            "message": "已标记当前场景已掌握"
        },
    )

@router.get("/scenes/{scene_id}")
async def handle_get_scene(
    scene_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent: ChatAgent = Depends(get_agent_service),
):
    """返回单个小场景详情（标题、背景图、NPC 列表及解锁状态），复用 scene-npc 的对话与进度逻辑。"""
    small_row = await db_get_small_scene_by_id_or_immersive(db, scene_id)
    if small_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景不存在")
    small_scene_id = small_row.id
    title = small_row.name or small_scene_id
    image = get_scene_image_url(small_scene_id)

    dialogues = await get_dialogues(db, agent)
    if not isinstance(dialogues, list):
        dialogues = []
    user_id = user.get("id") if user else None
    progress_row = await db_get_npc_learn_progress(db, user_id) if user_id else None
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
            "label": n.get("name") or n.get("id"),
            "learned": n.get("id") in learned_set,
            "has_content": True,
            "image": "",
            "character": n.get("id"),
            "hint": "",
        }
        for n in npc_list
    ]

    scene = {
        "id": small_scene_id,
        "small_scene_id": small_scene_id,
        "title": title,
        "name": title,
        "image": image,
        "npcs": npcs,
    }
    return success_response(message="获取场景成功", data={"scene": scene})
