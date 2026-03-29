"""
场景相关表：大场景、小场景。
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Index, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class BigScene(Base):
    """
    大场景表：如 daily、food、travel 等，对应 scene_npc_index 的 big_scenes。
    """
    __tablename__ = "big_scene"
    __table_args__ = (Index("idx_big_scene_order", "sort_order"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, comment="大场景ID，如 daily、food")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="显示名称，如 日常生活")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=99, comment="排序序号")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    small_scenes: Mapped[List["SmallScene"]] = relationship(
        "SmallScene",
        back_populates="big_scene",
        lazy="selectin",
        order_by="SmallScene.sort_order",
    )

    def to_dict(self):
        """将 Dialogue ORM 转为与 JSON 一致的 dict（含 big_scene、small_scene、content 为 list）。"""
        return {
            "id": self.id,
            "name": self.name,
            "order": self.sort_order
        }


class SmallScene(Base):
    """
    小场景表：如 home、cafe、airport 等，归属某大场景。
    """
    __tablename__ = "small_scene"
    __table_args__ = (
        Index("idx_small_scene_big", "big_scene_id"),
        Index("idx_small_scene_order", "sort_order"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, comment="小场景ID，如 home、cafe")
    big_scene_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("big_scene.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属大场景ID",
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="显示名称")
    immersive_scene_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="沉浸式场景ID（可与 id 不同，如 hospital->clinic）",
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序序号")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    big_scene: Mapped["BigScene"] = relationship("BigScene", back_populates="small_scenes")

    def to_dict(self):
        """将 Dialogue ORM 转为与 JSON 一致的 dict（含 big_scene、small_scene、content 为 list）。"""
        return {
            "id": self.id,
            "big_scene_id": self.big_scene_id,
            "name": self.name,
            "immersive_scene_id": self.immersive_scene_id,
            "order": self.sort_order
        }
