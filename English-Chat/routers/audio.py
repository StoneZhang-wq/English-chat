import json
import asyncio
import base64
import aiofiles
import os
from starlette import status
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from service.agent import ChatAgent, get_agent_service
from utils.auth import get_current_user
from config import configer
from utils import logger
from utils.response import success_response
from service.database import get_db

router = APIRouter(prefix="/api/audio", tags=["audio"])

@router.get("/tts/{file_path:path}")
async def serve_audio(file_path: str, user:dict=Depends(get_current_user)):
    """提供音频文件服务"""
    # 构建音频文件路径
    current_file_dir = os.path.join(configer.data_path, "audio", "tts")
    audio_path = os.path.join(current_file_dir, os.path.join(str(user["id"]), file_path))
    # 检查文件是否存在
    if os.path.exists(audio_path) and os.path.isfile(audio_path):
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            headers={"Content-Disposition": f"inline; filename={os.path.basename(audio_path)}"}
        )
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")


@router.get("/english_dialogue/{dialogue_id}/{file_path:path}")
async def serve_audio(dialogue_id: str, file_path: str, user:dict=Depends(get_current_user)):
    """提供音频文件服务"""
    # 构建音频文件路径
    current_file_dir = os.path.join(configer.data_path, "english_dialogue", dialogue_id)
    audio_path = os.path.join(current_file_dir, file_path)
    # 检查文件是否存在
    if os.path.exists(audio_path) and os.path.isfile(audio_path):
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            headers={"Content-Disposition": f"inline; filename={os.path.basename(audio_path)}"}
        )
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")


# 提供给火山引擎临时获取音频文件，不提供给客户端使用
@router.get("/temp/{token}")
async def serve_audio_temp(token: str,
                           agent: ChatAgent = Depends(get_agent_service)):
    """豆包录音文件识别拉取音频用：根据 token 从 cache 取路径并返回临时 wav 文件。"""
    path = await agent.cache.get(agent.AUDIO_TEMP_KEY_PREFIX + token)
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"temp audio Not found")

    return FileResponse(path, media_type="audio/wav")
