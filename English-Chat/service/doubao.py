import os
import json
import uuid
import asyncio
from typing import Optional
from pathlib import Path
import aiohttp
import websockets
from config import configer
from utils import logger
from utils.tools import write_audio
from typing import Dict, List, Optional


class DoubaoTTSClient:
    """豆包TTS客户端（火山引擎 - WebSocket）"""

    def __init__(self, app_id: str = None, access_token: str = None,
                 endpoint: str = None, voice_type: str = None, encoding: str = None):
        self.app_id = app_id or configer.volcengine_app_id
        self.access_token = access_token or configer.volcengine_access_token
        self.endpoint = endpoint or configer.tts_endpoint
        self.voice_type = voice_type or configer.tts_voice_type
        self.encoding = encoding or configer.tts_encoding

        if not self.app_id or not self.access_token:
            raise ValueError("请设置VOLCENGINE_APP_ID和VOLCENGINE_ACCESS_TOKEN环境变量")

    def _get_cluster(self, voice: str) -> str:
        """根据音色类型确定cluster"""
        if voice.startswith("S_"):
            return "volcano_icl"
        return "volcano_tts"

    async def _synthesize_async(self, text: str, voice_type: str = None, encoding: str = None) -> Optional[bytes]:
        """
        文字转语音（异步WebSocket实现）

        Args:
            text: 要合成的文本
            voice_type: 音色类型（可选，默认使用配置）
            encoding: 编码格式（可选，默认使用配置）

        Returns:
            音频数据（bytes）
        """
        if not text or not text.strip():
            return None

        voice_type = voice_type or self.voice_type
        encoding = encoding or self.encoding
        cluster = self._get_cluster(voice_type)

        # 导入protocols模块
        try:
            from .protocols import MsgType, full_client_request, receive_message
        except ImportError:
            logger.error("错误: 无法导入protocols模块，请确保protocols目录存在")
            return None

        # 连接WebSocket
        headers = {
            "Authorization": f"Bearer;{self.access_token}",
        }

        try:
            # 豆包 TTS 服务建连可能较慢，延长连接超时时间
            websocket = await websockets.connect(
                self.endpoint,
                additional_headers=headers,
                max_size=10 * 1024 * 1024,
                open_timeout=60,
                close_timeout=10
            )

            try:
                # 构建请求
                request = {
                    "app": {
                        "appid": self.app_id,
                        "token": self.access_token,
                        "cluster": cluster,
                    },
                    "user": {
                        "uid": str(uuid.uuid4()),
                    },
                    "audio": {
                        "voice_type": voice_type,
                        "encoding": encoding,
                    },
                    "request": {
                        "reqid": str(uuid.uuid4()),
                        "text": text,
                        "operation": "submit",  # 关键：必须包含operation字段
                        "with_timestamp": "1",
                        "extra_param": json.dumps({
                            "disable_markdown_filter": False,
                        }),
                    },
                }

                # 发送请求
                await full_client_request(websocket, json.dumps(request).encode())

                # 接收音频数据
                audio_data = bytearray()
                while True:
                    msg = await receive_message(websocket)

                    if msg.type == MsgType.FrontEndResultServer:
                        continue
                    elif msg.type == MsgType.AudioOnlyServer:
                        audio_data.extend(msg.payload)
                        if msg.sequence < 0:  # 最后一条消息
                            break
                    elif msg.type == MsgType.Error:
                        error_msg = msg.payload.decode('utf-8', errors='ignore') if msg.payload else "未知错误"
                        logger.error(f"TTS API错误: {error_msg}, 错误码: {msg.error_code}")
                        return None
                    else:
                        logger.error(f"TTS收到未知消息类型: {msg.type}, 消息: {msg}")
                        # 继续接收，可能还有音频数据
                        continue

                # 检查是否收到音频数据
                if not audio_data:
                    logger.error("未收到音频数据")
                    return None

                return bytes(audio_data)

            finally:
                await websocket.close()

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"TTS WebSocket连接失败:\n{error_trace}")
            return None

    def synthesize(self, text: str, voice_type: str = None, encoding: str = None) -> Optional[bytes]:
        """
        文字转语音（同步包装器）
        Args:
            text: 要合成的文本
            voice_type: 音色类型（可选）
            encoding: 编码格式（可选）

        Returns:
            音频数据（bytes）
        """
        try:
            # 尝试获取现有的事件循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                # 如果没有事件循环，创建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 如果事件循环正在运行（比如在Flask中），需要使用nest_asyncio
            # 或者使用线程来运行异步代码
            try:
                return loop.run_until_complete(self._synthesize_async(text, voice_type, encoding))
            except RuntimeError as e:
                if "This event loop is already running" in str(e):
                    # 在已有事件循环中运行，需要使用线程
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(self._synthesize_async(text, voice_type, encoding))
                        )
                        return future.result(timeout=30)
                else:
                    raise
        except Exception as e:
            import traceback
            logger.error(f"TTS synthesize错误:\n{traceback.format_exc()}")
            return None


class DoubaoASRClient:
    """豆包录音文件识别（火山引擎 File ASR）。提交音频 URL，轮询获取转写结果。"""

    def __init__(
        self,
        app_id: Optional[str] = None,
        access_token: Optional[str] = None,
        resource_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.app_id = (app_id or configer.volcengine_asr_app_id or "").strip()
        self.access_token = (access_token or configer.volcengine_asr_access_token or "").strip()
        self.resource_id = (resource_id or configer.volcengine_file_asr_resource_id or "volc.bigasr.auc").strip()
        # submit/query 必须发往火山引擎 ASR 接口，不能用 public_app_url（后者仅用于豆包拉取本应用临时音频的地址）
        self.base_url = (base_url or getattr(configer, "volcengine_asr_base_url", None) or "https://openspeech.bytedance.com").strip().rstrip("/")
        if not self.app_id or not self.access_token:
            raise ValueError("请设置 VOLCENGINE_ASR_APP_ID 和 VOLCENGINE_ASR_ACCESS_TOKEN")

    async def transcribe(self, audio_url: str) -> str:
        """提交音频 URL，轮询查询转写结果。返回转写文本。"""
        submit_url = f"{self.base_url}/api/v3/auc/bigmodel/submit"
        query_url = f"{self.base_url}/api/v3/auc/bigmodel/query"
        task_id = uuid.uuid4().hex
        headers_submit = {
            "Content-Type": "application/json",
            "X-Api-App-Key": self.app_id,
            "X-Api-Access-Key": self.access_token,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Request-Id": task_id,
            "X-Api-Sequence": "-1",
        }
        body = {
            "user": {"uid": "voice_chat_user"},
            "audio": {"url": audio_url, "format": "wav"},
            "request": {"model_name": "bigmodel", "enable_itn": True},
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(submit_url, json=body, headers=headers_submit) as resp:
                code = resp.headers.get("X-Api-Status-Code", "")
                if code != "20000000":
                    msg = resp.headers.get("X-Api-Message", await resp.text())
                    raise ValueError(f"录音文件识别提交失败: {code} - {msg}")
                x_tt_logid = resp.headers.get("X-Tt-Logid", "")
            headers_query = {
                "Content-Type": "application/json",
                "X-Api-App-Key": self.app_id,
                "X-Api-Access-Key": self.access_token,
                "X-Api-Resource-Id": self.resource_id,
                "X-Api-Request-Id": task_id,
                "X-Tt-Logid": x_tt_logid,
            }
            for _ in range(60):
                await asyncio.sleep(1)
                async with session.post(query_url, json={}, headers=headers_query) as qresp:
                    code = qresp.headers.get("X-Api-Status-Code", "")
                    if code == "20000000":
                        data = await qresp.json()
                        result = (data or {}).get("result") or {}
                        text = (result.get("text") or "").strip()
                        return text or ""
                    # 20000003：静音/无有效语音，视为识别结束但无文本，不抛错
                    if code == "20000003":
                        return ""
                    if code not in ("20000001", "20000002"):
                        msg = qresp.headers.get("X-Api-Message", await qresp.text())
                        raise ValueError(f"录音文件识别查询失败: {code} - {msg}")
        raise ValueError("录音文件识别查询超时")


class DouBaoAIService:
    def __init__(self):
        self.doubao_tts_client = None
        tts_p = (configer.tts_provider or "doubao").strip().lower()
        if tts_p == "doubao":
            try:
                if configer.volcengine_app_id and configer.volcengine_access_token:
                    self.doubao_tts_client = DoubaoTTSClient()
                else:
                    logger.warning("TTS_PROVIDER=doubao 但未配置 VOLCENGINE_APP_ID / VOLCENGINE_ACCESS_TOKEN")
            except ValueError as e:
                logger.warning("豆包 TTS 客户端初始化失败: %s", e)
        elif tts_p != "piper":
            logger.warning("未知 TTS_PROVIDER=%s，TTS 可能不可用", configer.tts_provider)

        self.doubao_asr_client = None
        asr_p = (getattr(configer, "asr_provider", "doubao") or "doubao").strip().lower()
        if asr_p == "doubao":
            try:
                if configer.volcengine_asr_app_id and configer.volcengine_asr_access_token:
                    self.doubao_asr_client = DoubaoASRClient()
                else:
                    logger.warning("ASR_PROVIDER=doubao 但未配置 VOLCENGINE_ASR_APP_ID / VOLCENGINE_ASR_ACCESS_TOKEN")
            except ValueError as e:
                logger.warning("豆包 ASR 客户端初始化失败: %s", e)

        # 限制 TTS 并发数，避免豆包 429 或本机 Piper/Whisper 过载
        limit = max(1, getattr(configer, "tts_concurrency_limit", 2))
        self._tts_semaphore = asyncio.Semaphore(limit)
        asr_lim = max(1, getattr(configer, "asr_concurrency_limit", 2))
        self._asr_semaphore = asyncio.Semaphore(asr_lim)

    async def generate_speech(self, text, output_path, user_id: int, channel:str, voice_type=None, conn_manager=None):
        try:
            if (configer.tts_provider or "doubao").strip().lower() == "piper":
                from . import local_speech

                async with self._tts_semaphore:
                    ok, err = await local_speech.synthesize_piper_async(text, output_path, voice_type)
                if ok:
                    return True
                logger.error("Piper TTS 失败: %s", err)
                if conn_manager:
                    await conn_manager.send_to_user_channel(
                        user_id, channel, json.dumps({"action": "error", "message": f"Piper TTS: {err}"})
                    )
                return False

            if not self.doubao_tts_client:
                if conn_manager:
                    await conn_manager.send_to_user_channel(
                        user_id, channel, json.dumps({"action": "error", "message": "豆包 TTS 未配置"})
                    )
                return False

            # 与 Piper 共用 _tts_semaphore；勿在 generate_tts_for_dialogue_lines 外层再套同一信号量（Piper 会死锁）
            async with self._tts_semaphore:
                audio_data = await asyncio.to_thread(self.doubao_tts_client.synthesize, text, voice_type)
                if audio_data:
                    file_extension = Path(output_path).suffix.lstrip('.').lower()
                    if file_extension == 'mp3':
                        await write_audio(output_path, audio_data)
                    else:
                        from pydub import AudioSegment
                        import io

                        audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))
                        audio_segment.export(output_path, format="wav")

                    return True
                if conn_manager:
                    await conn_manager.send_to_user_channel(
                        user_id,
                        channel,
                        json.dumps({"action": "error", "message": "豆包TTS生成失败：返回空数据"}),
                    )
                return False

        except Exception as e:
            logger.error(f"Error during Doubao TTS generation: {e}")
            if conn_manager:
                await conn_manager.send_to_user_channel(
                    user_id,
                    channel,
                    json.dumps({"action": "error", "message": f"豆包TTS错误: {str(e)}"}),
                )
            return False

    def attach_existing_dialogue_audio_urls(self, dialogue_lines: List[Dict], dialogue_id: str) -> None:
        """
        仅根据 data/english_dialogue/{dialogue_id}/ 下已有文件填充每行 audio_url，不调用 TTS。
        命名与 generate_tts_one_line 一致：{speaker}_{index}.(mp3|wav)，优先 TTS_ENCODING 对应后缀，否则尝试另一种。
        """
        if not dialogue_lines:
            return
        audio_dir = os.path.join(configer.data_path, "english_dialogue", dialogue_id)
        enc = (configer.tts_encoding or "mp3").strip().lower()
        primary = "mp3" if enc == "mp3" else "wav"
        secondary = "wav" if primary == "mp3" else "mp3"
        attached = 0
        for index, line in enumerate(dialogue_lines):
            speaker = line.get("speaker", "A")
            line["audio_url"] = None
            for ext in (primary, secondary):
                audio_filename = f"{speaker}_{index}.{ext}"
                audio_path = os.path.join(audio_dir, audio_filename)
                if os.path.isfile(audio_path) and os.path.getsize(audio_path) > 0:
                    line["audio_url"] = f"/api/audio/english_dialogue/{dialogue_id}/{audio_filename}"
                    attached += 1
                    break
        logger.info(
            "attach_existing_dialogue_audio_urls: dialogue_id=%s attached %d/%d (no TTS)",
            dialogue_id,
            attached,
            len(dialogue_lines),
        )

    async def generate_tts_one_line(self, line: Dict, index: int, dialogue_id: str, audio_dir: str, tts_encoding: str,
                                    user_id: int, channel:str, conn_manager=None):
        try:
            speaker = line.get("speaker", "A")
            if tts_encoding == "mp3":
                audio_filename = f"{speaker}_{index}.mp3"
            else:
                audio_filename = f"{speaker}_{index}.wav"

            audio_path = os.path.join(audio_dir, audio_filename)
            if os.path.exists(audio_path):
                line["audio_url"] = f"/api/audio/english_dialogue/{dialogue_id}/{audio_filename}"
                return

            voice_type_a = configer.tts_voice_type
            voice_type_b = configer.tts_voice_type_b
            voice_type = voice_type_b if speaker == "B" and voice_type_b else voice_type_a
            success = await self.generate_speech(line["text"], audio_path, user_id, channel, voice_type=voice_type, conn_manager=conn_manager)
            if not success and speaker == "B" and voice_type_b and voice_type_b != voice_type_a:
                logger.info("角色 B 人声 %s 不可用，回退使用 A 人声", voice_type_b)
                success = await self.generate_speech(line["text"], audio_path, user_id, channel, voice_type=voice_type_a, conn_manager=conn_manager)

            if not success:
                line["audio_url"] = None
                return

            if success and os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                line["audio_url"] = f"/api/audio/english_dialogue/{dialogue_id}/{audio_filename}"
            else:
                line["audio_url"] = None
        except Exception as e:
            logger.warning("生成音频 line %d 失败: %s", index, e)
            line["audio_url"] = None

    async def generate_tts_for_dialogue_lines(self, dialogue_lines: List[Dict], dialogue_id: str,
                                              user_id: int, channel: str, conn_manager=None,
                                              start_index: int = 0) -> None:
        """为 dialogue_lines 每行生成 TTS 音频，填充 audio_url。并发由 generate_speech 内 _tts_semaphore 统一限制。
        start_index: 首条在目录中的序号，用于多轮对话时避免覆盖（如沉浸式每轮 A_0, A_1, ...）。"""
        audio_dir = os.path.join(configer.data_path, "english_dialogue", dialogue_id)
        try:
            os.makedirs(audio_dir, exist_ok=True)
        except Exception as e:
            logger.warning("创建音频目录失败: %s", e)
            return

        tasks = [
            self.generate_tts_one_line(
                line,
                start_index + i,
                dialogue_id,
                audio_dir,
                configer.tts_encoding,
                user_id,
                channel,
                conn_manager,
            )
            for i, line in enumerate(dialogue_lines)
        ]
        await asyncio.gather(*tasks)


doubao_service = DouBaoAIService()


def get_doubao_service():
    return doubao_service
