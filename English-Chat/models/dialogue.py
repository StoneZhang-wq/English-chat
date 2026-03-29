"""
对话配置表：每段对话对应一条记录，含对话内容、大/小场景、NPC 等，并关联大场景表与小场景表。
"""
from datetime import datetime
from typing import Optional

import json
from sqlalchemy import Index, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Dialogue(Base):
    """
    对话配置表：一条记录为一段对话，含 content、大场景、小场景、npc 及描述字段，关联 big_scene.id 与 small_scene.id。
    """
    __tablename__ = "dialogue"
    __table_args__ = (
        Index("idx_dialogue_big_small", "big_scene_id", "small_scene_id"),
        Index("idx_dialogue_usage", "usage"),
        Index("idx_dialogue_id_unique", "dialogue_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键")
    dialogue_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="业务唯一ID，如 DL-HOME-FAMILY-1",
    )
    big_scene_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("big_scene.id", ondelete="RESTRICT"),
        nullable=False,
        comment="大场景ID，关联 big_scene 表",
    )
    small_scene_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("small_scene.id", ondelete="RESTRICT"),
        nullable=False,
        comment="小场景ID，关联 small_scene 表",
    )
    npc: Mapped[str] = mapped_column(String(64), nullable=False, comment="NPC 标识，如 family、waiter")
    dialogue_set: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="对话集序号")
    usage: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="用途：learn / review / immersive",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="对话内容 JSON 数组 [{role, content, hint}]")
    core_sentences: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="核心句型")
    core_chunks: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="核心词组")
    big_scene_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="大场景名称")
    small_scene_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="小场景名称")
    npc_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="NPC 名称")
    user_goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="用户（角色B）目标说明")
    user_goal_a: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="用户（角色A）目标说明")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    big_scene: Mapped["BigScene"] = relationship("BigScene", backref="dialogues", lazy="selectin")
    small_scene: Mapped["SmallScene"] = relationship("SmallScene", backref="dialogues", lazy="selectin")

    def to_dict(self):
        """将 Dialogue ORM 转为与 JSON 一致的 dict（含 big_scene、small_scene、content 为 list）。"""
        content = self.content
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                content = []
        return {
            "id": self.id,
            "dialogue_id": self.dialogue_id,
            "big_scene_id": self.big_scene_id,
            "small_scene_id": self.small_scene_id,
            "npc": self.npc,
            "dialogue_set": self.dialogue_set,
            "usage": self.usage,
            "content": content,
            "core_sentences": self.core_sentences,
            "core_chunks": self.core_chunks,
            "big_scene_name": self.big_scene_name,
            "small_scene_name": self.small_scene_name,
            "npc_name": self.npc_name,
            "user_goal": getattr(self, "user_goal", None),
            "user_goal_a": getattr(self, "user_goal_a", None),
        }