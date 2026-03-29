"""
WebSocket路由 - 实时通信
"""
import json
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from typing import List, Optional

from service.agent import ChatAgent, get_agent_service
from utils import logger

router = APIRouter()


def _get_websocket_query(websocket: WebSocket) -> dict:
    """从 WebSocket 连接 query 中解析参数（建连时前端传入 user_id、channel）"""
    query_string = websocket.scope.get("query_string") or b""
    if isinstance(query_string, bytes):
        query_string = query_string.decode("utf-8")
    params = parse_qs(query_string)
    return {k: (v[0] if v else None) for k, v in params.items()}


def _get_websocket_user_id(websocket: WebSocket) -> Optional[str]:
    values = _get_websocket_query(websocket).get("user_id")
    return values if isinstance(values, str) else None


async def _handle_ping(message: dict, websocket: WebSocket) -> dict:
    return {"action": "pong"}


async def _handle_set_account(message: dict, websocket: WebSocket) -> dict:
    return {"action": "account_set", "account_name": message.get("account_name", "")}


async def _handle_stop(message: dict, websocket: WebSocket) -> dict:
    return {"message": "Conversation stopped"}


async def _handle_start(message: dict, websocket: WebSocket) -> dict:
    return {"message": "Conversation started", "action": "waiting"}


async def _handle_set_character(message: dict, websocket: WebSocket) -> dict:
    return {"message": f"Character: {message.get('character')}"}


async def _handle_clear(message: dict, websocket: WebSocket) -> dict:
    return {"message": "Conversation history cleared."}


async def _handle_unknown(message: dict, websocket: WebSocket) -> dict:
    action = message.get("action")
    return {"status": "received", "action": action}


# 动作分发表：避免主流程中大量 if-else
_ACTION_HANDLERS = {
    "ping": _handle_ping,
    "set_account": _handle_set_account,
    "stop": _handle_stop,
    "start": _handle_start,
    "set_character": _handle_set_character,
    "clear": _handle_clear,
}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, agent: ChatAgent = Depends(get_agent_service)):
    """标准WebSocket端点；建连时可带 query 参数 user_id、channel（缺省 channel=main）"""
    q = _get_websocket_query(websocket)
    user_id = q.get("user_id")
    channel = q.get("channel") or "main"
    if user_id:
        logger.info("WebSocket connect user_id=%s channel=%s", user_id, channel)
    await agent.conn_manager.connect(websocket, user_id=user_id, channel=channel)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                logger.info(f"message={message}")
                action = message.get("action")
                handler = _ACTION_HANDLERS.get(action, _handle_unknown)
                payload = await handler(message, websocket)
                await agent.conn_manager.send_message(payload, websocket)
            except json.JSONDecodeError:
                await agent.conn_manager.send_message({"error": "Invalid JSON"}, websocket)
    except WebSocketDisconnect:
        agent.conn_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")


@router.websocket("/ws_enhanced")
async def websocket_enhanced_endpoint(websocket: WebSocket, agent: ChatAgent = Depends(get_agent_service)):
    """增强版WebSocket端点；建连时可带 query 参数 user_id、channel（缺省 channel=enhanced）"""
    q = _get_websocket_query(websocket)
    user_id = q.get("user_id")
    channel = q.get("channel") or "enhanced"
    if user_id:
        logger.info("WebSocket (enhanced) connect user_id=%s channel=%s", user_id, channel)
    await agent.conn_manager.connect(websocket, user_id=user_id, channel=channel)
    try:
        # 发送连接确认
        await websocket.send_json({"action": "connected"})
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "ping":
                    await websocket.send_json({"action": "pong"})
                else:
                    # 通用响应
                    await websocket.send_json({"status": "ok", "action": action})
                    
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                
    except WebSocketDisconnect:
        agent.conn_manager.disconnect(websocket)
        logger.error("Enhanced WebSocket client disconnected")