from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.diary import Diary


async def db_create_diary(db: AsyncSession, user_id: int, content: str, scene_type: int = None, session_id: str = None):
    """创建一条日记。"""
    diary = Diary(user_id=user_id, content=content, scene_type=scene_type, session_id=session_id)
    db.add(diary)
    await db.commit()
    await db.refresh(diary)
    return diary


async def db_get_diary(db: AsyncSession, diary_id: int):
    """按主键获取日记。"""
    query = select(Diary).where(Diary.id == diary_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def db_list_diaries_by_user(db: AsyncSession, user_id: int, limit: int = 100):
    """按用户获取日记列表，按创建时间倒序。"""
    query = (
        select(Diary)
        .where(Diary.user_id == user_id)
        .order_by(desc(Diary.created_at))
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def db_delete_diary(db: AsyncSession, diary_id: int, user_id: int = None):
    """删除一条日记；若传入 user_id 则校验归属。"""
    stmt = delete(Diary).where(Diary.id == diary_id)
    if user_id is not None:
        stmt = stmt.where(Diary.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
