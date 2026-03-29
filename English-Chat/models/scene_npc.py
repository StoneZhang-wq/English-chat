"""
NPC 学习进度表：按用户存储已学对话，与 Dialogue 表通过 dialogue_id 关联。
process 为 JSON 字符串数组，记录用户已学习的 dialogue_id 列表。
"""
from datetime import datetime
from typing import Optional

import json
from sqlalchemy import Index, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, generate_uuid
from utils import logger


class NpcLearnProgress(Base):
    """
    NPC 学习进度表：每用户一条，process 存 JSON 数组 [dialogue_id, ...]，表示用户学过的对话。
    与 Dialogue 表通过 dialogue_id 逻辑关联。
    """
    __tablename__ = "npc_learn_progress"
    __table_args__ = (Index("idx_npc_learn_progress_user", "user_id"),)

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: generate_uuid(),
        comment="学习进度ID",
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属用户ID",
    )
    process: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="已学对话 ID 列表的 JSON 数组，如 [\"DL-HOME-FAMILY-1\", \"DL-CAFE-WAITER-1\"]",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    def to_process_list(self):
        if not self.process or self.process == "":
            return set()
        try:
            parsed = json.loads(self.process)
            if isinstance(parsed, list):
                user_process_set = {x for x in parsed if isinstance(x, str) and x.strip()}
                return user_process_set
        except (TypeError, json.JSONDecodeError):
            logger.error(f"获取用户学习进度列表失败")

        return set()
