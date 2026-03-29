"""
本地语音识别（faster-whisper）与朗读合成（Piper CLI）。

使用前请自行下载：
- Whisper：首次运行 faster-whisper 会自动拉取模型到本地缓存。
- Piper：从 https://github.com/rhasspy/piper/releases 下载对应平台的 piper 可执行文件，
  从 https://huggingface.co/rhasspy/piper-voices 等获取 .onnx 与同名的 .onnx.json，放在任意目录，
  通过环境变量 PIPER_VOICE_EN / PIPER_VOICE_ZH / PIPER_VOICE_EN_B 指向 .onnx 路径。
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, Tuple

from config import configer
from utils import logger

_whisper_model = None
_whisper_lock = threading.Lock()


def _get_whisper_model():
    global _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            from faster_whisper import WhisperModel

            size = (configer.local_whisper_model_size or "base").strip()
            device = (configer.local_whisper_device or "cpu").strip()
            compute = (configer.local_whisper_compute_type or "int8").strip()
            logger.info(
                "ASR: 开始加载 faster-whisper（首次会从 Hugging Face 下载并缓存，可能需数分钟）"
                " model=%s device=%s compute_type=%s",
                size,
                device,
                compute,
            )
            t0 = time.monotonic()
            _whisper_model = WhisperModel(size, device=device, compute_type=compute)
            logger.info("ASR: faster-whisper 模型已载入内存，耗时 %.1fs", time.monotonic() - t0)
        return _whisper_model


def transcribe_file_sync(audio_path: str) -> str:
    """同步：对本地音频文件转写，返回文本。"""
    path = Path(audio_path)
    if not path.is_file():
        logger.error("ASR: file not found: %s", audio_path)
        return ""
    try:
        sz = path.stat().st_size
    except OSError:
        sz = -1
    logger.info("ASR: 准备转写文件 path=%s size_bytes=%s", path, sz)

    model = _get_whisper_model()
    lang = (configer.local_whisper_language or "").strip() or None
    logger.info("ASR: 开始解码/转写（CPU 较慢时请耐心等待） language=%s", lang or "auto")
    t1 = time.monotonic()
    segments, info = model.transcribe(str(path), language=lang)
    parts = [s.text.strip() for s in segments if s.text and s.text.strip()]
    text = " ".join(parts).strip()
    elapsed = time.monotonic() - t1
    audio_dur = getattr(info, "duration", None)
    detected = getattr(info, "language", None)
    logger.info(
        "ASR: 转写完成 elapsed=%.1fs audio_duration=%s detected_language=%s text_len=%d",
        elapsed,
        f"{audio_dur:.2f}s" if audio_dur is not None else "n/a",
        detected or "n/a",
        len(text),
    )
    return text


def _resolve_piper_model(voice_type: Optional[str]) -> Optional[str]:
    """根据豆包音色占位参数选择 Piper 模型路径。"""
    vt = (voice_type or "").strip()
    zh_path = (configer.piper_voice_zh or "").strip()
    en_b_path = (configer.piper_voice_en_b or "").strip()
    en_path = (configer.piper_voice_en or "").strip()
    zh_hint = configer.tts_voice_type_zh or ""
    en_b_hint = configer.tts_voice_type_b or ""

    if zh_path and (vt == zh_hint or "zh_" in vt or vt.startswith("zh")):
        return zh_path if Path(zh_path).is_file() else None
    if en_b_path and vt and en_b_hint and vt == en_b_hint:
        return en_b_path if Path(en_b_path).is_file() else None
    if en_path and Path(en_path).is_file():
        return en_path
    if zh_path and Path(zh_path).is_file():
        return zh_path
    return en_path if en_path else None


def synthesize_piper_sync(text: str, output_path: str, voice_type: Optional[str] = None) -> Tuple[bool, str]:
    """
    同步：Piper 合成。output_path 可为 .wav 或 .mp3（mp3 时先写临时 wav 再 pydub 转码）。
    返回 (success, error_message)。
    """
    text = (text or "").strip()
    if not text:
        return False, "empty text"

    model_path = _resolve_piper_model(voice_type)
    if not model_path:
        return False, "PIPER_VOICE_EN（或中文 PIPER_VOICE_ZH）未配置或文件不存在"

    exe = (configer.piper_executable or "piper").strip()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.suffix.lower() == ".wav":
        wav_final = out
        tmp_wav = None
    else:
        tmp_wav = out.with_suffix(".wav")
        wav_final = tmp_wav

    try:
        cmd = [exe, "--model", str(Path(model_path).resolve()), "--output_file", str(wav_final.resolve())]
        proc = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=max(30, len(text) // 5 + 30),
        )
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="ignore") or proc.stdout.decode("utf-8", errors="ignore")
            return False, err or f"piper exit {proc.returncode}"

        if not wav_final.is_file() or wav_final.stat().st_size == 0:
            return False, "piper produced empty output"

        if tmp_wav is not None:
            from pydub import AudioSegment

            seg = AudioSegment.from_wav(str(wav_final))
            ext = out.suffix.lower().lstrip(".") or "mp3"
            seg.export(str(out), format=ext)
            try:
                wav_final.unlink(missing_ok=True)
            except OSError:
                pass

        return True, ""
    except FileNotFoundError:
        return False, f"Piper 可执行文件未找到: {exe}（请安装 Piper 并配置 PIPER_EXECUTABLE）"
    except subprocess.TimeoutExpired:
        return False, "piper timeout"
    except Exception as e:
        logger.exception("Piper synthesize failed: %s", e)
        return False, str(e)


async def transcribe_file_async(audio_path: str) -> str:
    return await asyncio.to_thread(transcribe_file_sync, audio_path)


async def synthesize_piper_async(text: str, output_path: str, voice_type: Optional[str] = None) -> Tuple[bool, str]:
    return await asyncio.to_thread(synthesize_piper_sync, text, output_path, voice_type)
