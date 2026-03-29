from datetime import datetime
from typing import Optional, List
from sqlalchemy import Index, Integer, String, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class User(Base):
    """
    用户信息表ORM模型
    """
    __tablename__ = 'users'
    # 创建索引
    __table_args__ = (
        Index('username_UNIQUE', 'username'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username: Mapped[str] = mapped_column(String(64), nullable=False, comment="用户名")
    email: Mapped[str] = mapped_column(String(128),  nullable=True, comment="用户邮箱")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码（加密存储）")
    avatar: Mapped[Optional[str]] = mapped_column(String(255), comment="头像URL", default='https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg')

    name: Mapped[str] = mapped_column(String(64), nullable=True, comment="姓名")
    english_level: Mapped[str] = mapped_column(String(64), nullable=False, default="beginner", comment="英语水平")
    age: Mapped[int] = mapped_column(Integer, nullable=False, default=24, comment="年龄")
    occupation: Mapped[str] = mapped_column(String(64), nullable=True, comment="职业")
    goals: Mapped[str] = mapped_column(String(64), nullable=True, comment="目标")
    habits: Mapped[str] = mapped_column(String(128), nullable=True, comment="习惯")
    interests: Mapped[str] = mapped_column(String(255), nullable=True, comment="兴趣爱好")
    preferences: Mapped[str] = mapped_column(String(255), nullable=True, comment="偏好")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), onupdate=datetime.now(), comment="更新时间")
    # 在线状态：登录时设为 True，登出时设为 False
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否在线")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'name': self.name,
            'english_level': self.english_level,
            'age': self.age,
            'occupation': self.occupation,
            'goals': self.goals,
            'habits': self.habits,
            'interests': self.interests,
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_online': self.is_online,
            "learning_stage": "chinese_chat"
        }


class UserToken(Base):
    """
    用户令牌表ORM模型
    """
    __tablename__ = 'user_token'

    # 创建索引
    __table_args__ = (
        Index('token_UNIQUE', 'token'),
        Index('fk_user_token_user_idx', 'user_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="令牌ID")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id, ondelete="CASCADE"), nullable=False, comment="用户ID")
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="令牌值")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), comment="创建时间")

    def __repr__(self):
        return f"<UserToken(id={self.id}, user_id={self.user_id}, token='{self.token}')>"