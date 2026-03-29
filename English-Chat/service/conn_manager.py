from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Optional, Tuple, Union
from utils import logger

# 默认频道：主聊天（voice_chat.js）
DEFAULT_CHANNEL = "main"

# WebSocket连接管理：按 (user_id, channel) 维护，只向指定用户的指定频道推送；user_id 统一为 str
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # (user_id, channel) -> 该用户该频道下的 WebSocket 列表（同 channel 多标签仍会多条）
        self._by_user_channel: Dict[Tuple[str, str], List[WebSocket]] = {}
        # 反向索引：连接 -> (user_id, channel)，便于 disconnect 时清理
        self._ws_to_key: Dict[WebSocket, Tuple[str, str]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, channel: str):
        await websocket.accept()
        self.active_connections.append(websocket)

        key = (str(user_id), channel)
        self._by_user_channel.setdefault(key, []).append(websocket)
        self._ws_to_key[websocket] = key

        logger.info(f"Connected to user {user_id} channel {channel}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self._ws_to_key:
            key = self._ws_to_key.pop(websocket)
            if key in self._by_user_channel:
                conns = self._by_user_channel[key]
                if websocket in conns:
                    conns.remove(websocket)
                if not conns:
                    del self._by_user_channel[key]

    @staticmethod
    async def send_message(message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")

    async def send_to_user_channel(self, user_id: int, channel: str, message: dict):
        """只向指定用户的指定频道发送（例如主聊天 channel=main），该用户其他 channel 的连接不会收到。user_id 可为 int 或 str，内部统一为 str。"""
        key = (str(user_id), channel)
        conns = self._by_user_channel.get(key) or []
        for ws in conns[:]:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id} channel {channel}: {e}")
                if ws in self.active_connections:
                    self.disconnect(ws)