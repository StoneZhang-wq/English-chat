import os
import re
import uuid
import time
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from config import configer
from crud.chat import (
    db_add_chat_message,
    db_create_chat_session,
    db_list_chat_messages,
    db_list_chat_sessions,
)
from models import ChatMessage
from models.base import SceneType
from .doubao import DouBaoAIService
from .openai import get_openai_service
from .gemini import get_gemini_service
from .prompt import adjust_prompt, get_study_prompt, get_time_prompt, get_user_profile_prompt
from utils import logger
from utils.tools import analyze_mood, read_file
from .redis_cache import AsyncRedisCache
from .conn_manager import ConnectionManager


def _normalize_client_session_id(session_id: Optional[str]) -> Optional[str]:
    """前端 FormData 在 session_id 为 null 时会变成字符串 'null'，须视为无会话。"""
    if session_id is None:
        return None
    s = str(session_id).strip()
    if not s or s.lower() in ("null", "undefined", "none"):
        return None
    return s


class ChatAgent:
    def __init__(self):
        self.llm = self._create_llm()
        self.cache = AsyncRedisCache(enable_stats=False)
        self.conn_manager = ConnectionManager()
        self.doubao_service = DouBaoAIService()
        self.gemini = None
        self.AUDIO_TEMP_KEY_PREFIX = "audio_temp:"
        self.AUDIO_TEMP_TTL = 300

    @staticmethod
    def _create_llm():
        if configer.openai_api_key and configer.openai_base_url:
            return get_openai_service()
        if configer.openai_api_key and not configer.openai_base_url:
            return get_openai_service()
        if configer.google_api_key:
            return get_gemini_service()
        logger.warning("No LLM provider configured. Set OPENAI_API_KEY or GOOGLE_API_KEY.")
        return None

    async def generate_chat(self, message: str,  history: list[ChatMessage],  system_prompt="", msg_limit=50) ->str:
        context_msg = []
        for msg in history[-msg_limit:]:
            context_msg.append({"role": msg.role, "content": msg.content})

        result = await self.llm.generate_chat(message, context_msg, system_prompt)
        response = self.sanitize_response(result)
        return response

    async def _register_audio_temp(self, file_path: str) -> str:
        token = uuid.uuid4().hex
        await self.cache.set(self.AUDIO_TEMP_KEY_PREFIX + token, file_path, ttl=self.AUDIO_TEMP_TTL)
        return token

    async def _unregister_audio_temp(self, token: str) -> None:
        await self.cache.delete(self.AUDIO_TEMP_KEY_PREFIX + token)

    async def transcribe_audio(self, tmp_file_path: str, base_url) -> str:
        """根据 ASR_PROVIDER：local 用 faster-whisper 读本地文件；doubao 用火山录音文件识别（需公网 URL）。"""
        if (configer.asr_provider or "doubao").strip().lower() == "local":
            from . import local_speech

            try:
                async with self.doubao_service._asr_semaphore:
                    return await local_speech.transcribe_file_async(tmp_file_path)
            except Exception as e:
                logger.error("local ASR failed: %s", e)
                return ""

        if not self.doubao_service.doubao_asr_client:
            logger.error("ASR_PROVIDER=doubao 但豆包 ASR 未初始化，请配置 VOLCENGINE_ASR_*")
            return ""

        # 豆包会 GET 此 URL 拉取音频，必须用本应用的公网 base（PUBLIC_APP_URL 或当前请求 base）
        app_base = (configer.public_app_url or str(base_url)).strip().rstrip("/")
        if not configer.public_app_url and app_base:
            logger.warning(
                "PUBLIC_APP_URL 未配置，使用请求 base_url=%s；若部署在内网/代理后，豆包无法拉取音频会导致转写失败，请设置环境变量 PUBLIC_APP_URL 为本应用公网地址",
                app_base,
            )
        token = await self._register_audio_temp(tmp_file_path)
        try:
            audio_url = f"{app_base}/api/audio/temp/{token}"
            return await self.doubao_service.doubao_asr_client.transcribe(audio_url)
        except Exception as e:
            logger.error(f"failed to transcribe audio: {e}")
        finally:
            await self._unregister_audio_temp(token)

        return ""

    async def generate_speech(self, prompt, character, learning_stage, user_id: int, channel: str):
        filename = f"{channel}_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000)}.wav"
        tts_dir = os.path.join(os.path.join(configer.data_path, "audio", "tts", str(user_id)))
        os.makedirs(tts_dir, exist_ok=True)
        output_path = os.path.join(tts_dir, filename)

        # 中文对话阶段必须用中文专用音色 TTS_VOICE_TYPE_ZH（仅说中文）；英文学习阶段用 TTS_VOICE_TYPE
        stage = learning_stage
        if stage == "chinese_chat":
            doubao_voice = configer.tts_voice_type_zh.strip() or "zh_female_cancan_mars_bigtts"
        else:
            doubao_voice = configer.tts_voice_type or "zh_female_cancan_mars_bigtts"
        success = await self.doubao_service.generate_speech(prompt, output_path, user_id, channel, voice_type=doubao_voice, conn_manager=self.conn_manager)
        if success and os.path.exists(output_path):
            audio_url = f"/api/audio/tts/{filename}"
            await self.conn_manager.send_to_user_channel(user_id,
                                                         channel,
                                                         {
                                                            "action": "ai_audio",
                                                            "audio_url": audio_url,
                                                            "character": character}
                                                         )
            logger.info(f"生成音频成功: {audio_url}")
        else:
            await self.conn_manager.send_to_user_channel(user_id,
                                                         channel,
                                                         {
                                                             "action": "error",
                                                             "text": "Error: TTS 生成失败（豆包或 Piper 配置）"}
                                                         )

    async def generate_chat_flow(
                                self,
                                db: AsyncSession,
                                user: dict,
                                character: str,
                                user_message: str,
                                scene_type: SceneType,
                                session_id: Optional[str] = None,
                                title: Optional[str] = None,
                                channel: str = "main"
                            ) -> Tuple[str, str]:
        """
        统一流程：取/建会话 → 拉历史 → 拼 prompt → 生成回复 → TTS → 落库。
        返回 (session_id, ai_text)。
        """
        user_id = user.get("id")
        learning_stage = user.get("learning_stage", "chinese_chat")
        session_id = _normalize_client_session_id(session_id)
        if session_id:
            history_msg = await db_list_chat_messages(db, session_id, character)
        else:
            session = await db_create_chat_session(db, user_id, int(scene_type.value), title=title or character)
            session_id = session.id
            history_msg = []

        char_path = os.path.join(configer.characters_folder, character)
        character_prompt_file = os.path.join(char_path, f"{character}.txt")
        base_prompt = await self.cache.get("character_prompt:" + character_prompt_file)
        if not base_prompt:
            base_prompt = await read_file(character_prompt_file)
            if base_prompt:
                await self.cache.set("character_prompt:" + character_prompt_file, base_prompt)

        time_prompt = get_time_prompt()
        user_prompt = get_user_profile_prompt(user)
        study_prompt = get_study_prompt(learning_stage, user)
        mood = analyze_mood(user_message)

        mood_prompt = await self.cache.get("mood_prompt:" +  character + ":" + mood)
        if not mood_prompt:
            mood_prompt = adjust_prompt(mood, character)
            if mood_prompt:
                await self.cache.set("mood_prompt:" +  character + ":" + mood, mood_prompt)

        system_prompt = base_prompt + time_prompt + user_prompt + study_prompt + mood_prompt

        ai_text = await self.generate_chat(user_message, history_msg, system_prompt)

        print(f"learning_stage: {learning_stage}")
        if learning_stage != "chinese_chat":
            await self.generate_speech(ai_text, character, learning_stage, user_id, channel)

        await db_add_chat_message(db, session_id, "user", user_message, character)
        await db_add_chat_message(db, session_id, "assistant", ai_text, character)

        return session_id, ai_text

    @staticmethod
    def sanitize_response(response):
        """
        清洗 LLM 回复中的噪声，但不要破坏 JSON/标点等结构化内容。

        之前的实现会移除 { } [ ] \" 等字符，导致需要 JSON 的接口（如 generate-review）
        无法解析出结构化结果。这里仅去除 <think> 块与包裹性星号格式，保留其余字符。
        """
        if not response:
            return ""
        # 1) 移除 <think>...</think>（部分模型会输出思考内容）
        response = re.sub(r"<think>[\s\S]*?</think>", "", response, flags=re.IGNORECASE)
        # 2) 移除成对的 *...*（轻量格式化），避免污染文本；不要做更激进的字符过滤
        response = re.sub(r"\*([^*]+)\*", r"\1", response)
        return response.strip()

    @staticmethod
    def extract_json_from_response(response: str) -> Optional[str]:
        """从 LLM 回复中提取 JSON：优先取 ```json 代码块内从第一个 { 到最后一个 }，否则整段取第一个 { 到最后一个 }。"""
        if not response or not response.strip():
            return None
        text = response
        # 1. 若有 ```json 或 ``` 代码块，只在代码块内找 JSON，避免 <think> 等里的 } 干扰
        code_fence = re.search(r"```(?:json)?\s*\n([\s\S]*?)```", response)
        if code_fence:
            text = code_fence.group(1)
        start = text.find("{")
        if start < 0:
            return None
        end = text.rfind("}")
        if end < start:
            return None
        return text[start: end + 1].strip()


AgentService = ChatAgent()


def get_agent_service():
    return AgentService