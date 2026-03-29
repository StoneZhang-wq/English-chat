from sqlalchemy import select, update, desc, delete, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.chat import ChatSession, ChatMessage


async def db_create_chat_session(db: AsyncSession,
                                 user_id: int,
                                 scene_type: int,
                                 title="New Chat"):
    chat_session = ChatSession(user_id=user_id, title=title, scene_type=scene_type)
    db.add(chat_session)
    await db.commit()
    await db.refresh(chat_session)
    return chat_session


async def db_get_chat_session(db: AsyncSession, session_id: str):
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def db_delete_chat_session(db: AsyncSession, session_id: str):
    stmt = delete(ChatSession).where(ChatSession.id == session_id)
    await db.execute(stmt)
    await db.commit()


async def db_list_chat_sessions(db: AsyncSession, user_id: int, scene_type: int):
    query = select(ChatSession).where((ChatSession.user_id == user_id) & (ChatSession.scene_type==scene_type)).order_by(desc(ChatSession.updated_at))
    result = await db.execute(query)
    return result.scalars().all()


async def db_add_chat_message(db: AsyncSession, session_id: str, role: str, content: str, character: str):
    chat_message = ChatMessage(session_id=session_id, role=role, content=content, character=character)
    db.add(chat_message)
    await db.commit()
    await db.refresh(chat_message)
    return chat_message


async def db_list_chat_messages(db: AsyncSession, session_id: str, character: str=None):
    if character:
        query = select(ChatMessage).where((ChatMessage.session_id == session_id) & (ChatMessage.character == character)).order_by(asc(ChatMessage.created_at))
    else:
        query = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(asc(ChatMessage.created_at))
    result = await db.execute(query)
    return result.scalars().all()


async def db_get_chat_message(db: AsyncSession, message_id: str):
    query = select(ChatMessage).where(ChatMessage.id == message_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def db_delete_chat_message(db: AsyncSession, message_id: str):
    stmt = delete(ChatMessage).where(ChatMessage.id == message_id)
    await db.execute(stmt)
    await db.commit()

