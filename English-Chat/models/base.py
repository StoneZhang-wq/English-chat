import uuid
import enum
from sqlalchemy.orm import DeclarativeBase

class SceneType(str, enum.Enum):
    """场景类型"""
    NATURAL_PRACTICE = 0     # 自然对话
    SCENE_PRACTICE = 1       # 场景对话
    AI_CHAT = 2        # AI对话
    REAL_MATCH = 3     # 真人匹配


def generate_uuid():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass
