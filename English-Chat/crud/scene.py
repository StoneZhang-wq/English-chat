from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession

from models.scene import BigScene, SmallScene


async def db_list_all_big_scenes(db: AsyncSession):
    """获取所有大场景，按 sort_order 升序。"""
    query = select(BigScene).order_by(asc(BigScene.sort_order))
    result = await db.execute(query)
    return result.scalars().all()


async def db_get_big_scene(db: AsyncSession, big_scene_id: str):
    """按 id 获取大场景。"""
    query = select(BigScene).where(BigScene.id == big_scene_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def db_list_all_small_scenes(db: AsyncSession):
    """获取所有小场景，按 big_scene_id、sort_order 升序。"""
    query = select(SmallScene).order_by(asc(SmallScene.big_scene_id), asc(SmallScene.sort_order))
    result = await db.execute(query)
    return result.scalars().all()


async def db_list_small_scenes_by_big(db: AsyncSession, big_scene_id: str):
    """获取某大场景下所有小场景，按 sort_order 升序。"""
    query = (
        select(SmallScene)
        .where(SmallScene.big_scene_id == big_scene_id)
        .order_by(asc(SmallScene.sort_order))
    )
    result = await db.execute(query)
    return result.scalars().all()


async def db_get_small_scene(db: AsyncSession, small_scene_id: str):
    """按 id 获取小场景。"""
    query = select(SmallScene).where(SmallScene.id == small_scene_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def db_get_small_scene_by_id_or_immersive(db: AsyncSession, scene_id: str):
    """按 id 或 immersive_scene_id 获取小场景（前端可能传任一种）。"""
    row = await db_get_small_scene(db, scene_id)
    if row is not None:
        return row
    query = select(SmallScene).where(SmallScene.immersive_scene_id == scene_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()
