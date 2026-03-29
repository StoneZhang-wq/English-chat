#!/usr/bin/env python3
"""检查本地 ASR（faster-whisper）与 Piper TTS 配置是否就绪。在项目根目录执行: python scripts/check_local_speech.py"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=True)

    asr = (os.getenv("ASR_PROVIDER") or "doubao").strip().lower()
    tts = (os.getenv("TTS_PROVIDER") or "doubao").strip().lower()
    print(f"ASR_PROVIDER={asr!r}  TTS_PROVIDER={tts!r}\n")

    ok = True

    if asr == "local":
        try:
            import faster_whisper  # noqa: F401

            print("[OK] faster-whisper 已安装")
        except ImportError:
            print("[FAIL] 未安装 faster-whisper，请执行: pip install faster-whisper")
            ok = False
        size = os.getenv("LOCAL_WHISPER_MODEL_SIZE", "base")
        print(f"     将使用模型: {size}（首次识别时会自动下载）")
    else:
        print(f"[--] ASR 非 local，跳过 Whisper 检查")

    if tts == "piper":
        exe = (os.getenv("PIPER_EXECUTABLE") or "piper").strip()
        voice = (os.getenv("PIPER_VOICE_EN") or "").strip()
        exe_path = Path(exe)
        if not exe_path.is_absolute():
            exe_path = (ROOT / exe).resolve()
        voice_path = Path(voice)
        if voice and not voice_path.is_absolute():
            voice_path = (ROOT / voice).resolve()

        if not exe_path.is_file():
            print(f"[FAIL] Piper 可执行文件不存在: {exe_path}")
            ok = False
        else:
            print(f"[OK] Piper 可执行文件: {exe_path}")

        json_path = voice_path.with_suffix(".onnx.json") if voice_path.suffix.lower() == ".onnx" else None
        if not voice_path.is_file():
            print(f"[FAIL] PIPER_VOICE_EN 模型不存在: {voice_path}")
            ok = False
        else:
            print(f"[OK] 英文音色模型: {voice_path}")
        if json_path and not json_path.is_file():
            print(f"[FAIL] 缺少同目录配置文件: {json_path}")
            ok = False
        elif json_path:
            print(f"[OK] 配置文件: {json_path}")

        if ok and exe_path.is_file() and voice_path.is_file():
            out_wav = ROOT / "models" / "piper" / "_check_test.wav"
            out_wav.parent.mkdir(parents=True, exist_ok=True)
            try:
                proc = subprocess.run(
                    [str(exe_path), "--model", str(voice_path), "--output_file", str(out_wav)],
                    input=b"Hello from English Chat check.",
                    capture_output=True,
                    timeout=60,
                    cwd=str(exe_path.parent),
                )
                if proc.returncode != 0 or not out_wav.is_file() or out_wav.stat().st_size < 100:
                    err = proc.stderr.decode("utf-8", errors="ignore")
                    print(f"[FAIL] Piper 试合成失败 (code={proc.returncode}): {err[:500]}")
                    ok = False
                else:
                    print(f"[OK] Piper 试合成成功: {out_wav} ({out_wav.stat().st_size} bytes)")
                    try:
                        out_wav.unlink()
                    except OSError:
                        pass
            except Exception as e:
                print(f"[FAIL] Piper  subprocess: {e}")
                ok = False
    else:
        print(f"[--] TTS 非 piper，跳过 Piper 检查")

    print()
    if ok:
        print("检查通过：可启动应用后测试语音上传与英文阶段 AI 朗读。")
        return 0
    print("请根据上述 [FAIL] 项修复后重试。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
