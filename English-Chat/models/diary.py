"""
学习日记表：用户的学习记录、心得等，可关联场景或会话。
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Index, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Diary(Base):
    """
    学习日记表：按条记录用户日记，可选关联场景类型或会话。
    """
    __tablename__ = "diary"
    __table_args__ = (
        Index("idx_diary_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属用户ID",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="日记内容")
    scene_type: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="关联场景类型（可选），如 SceneType",
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="关联会话ID（可选）",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )
