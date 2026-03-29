from sqlalchemy import select, asc, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from models.dialogue import Dialogue


async def db_list_all_dialogues(db: AsyncSession):
    """获取所有对话配置，无排序要求时用于全量加载。"""
    result = await db.execute(select(Dialogue))
    return result.scalars().all()


async def db_list_distinct_small_scene_ids_immersive(db: AsyncSession):
    """返回有 usage=immersive 的 dialogue 的 small_scene_id 去重列表。"""
    result = await db.execute(
        select(distinct(Dialogue.small_scene_id)).where(Dialogue.usage == "immersive")
    )
    return [row[0] for row in result.fetchall() if row[0]]

async def db_list_distinct_small_scene_ids_learn(db: AsyncSession):
    """返回有 usage=learn 的 dialogue 的 small_scene_id 去重列表。"""
    result = await db.execute(
        select(distinct(Dialogue.small_scene_id)).where(Dialogue.usage == "learn")
    )
    return [row[0] for row in result.fetchall() if row[0]]

async def db_list_distinct_small_scene_ids_review(db: AsyncSession):
    """返回有 usage=learn 的 dialogue 的 small_scene_id 去重列表。"""
    result = await db.execute(
        select(distinct(Dialogue.small_scene_id)).where(Dialogue.usage == "review")
    )
    return [row[0] for row in result.fetchall() if row[0]]


async def db_get_dialogue_by_dialogue_id(db: AsyncSession, dialogue_id: str):
    """按业务唯一 dialogue_id 获取一条对话配置。"""
    query = select(Dialogue).where(Dialogue.dialogue_id == dialogue_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def db_get_dialogue(db: AsyncSession, pk: int):
    """按主键获取对话。"""
    query = select(Dialogue).where(Dialogue.id == pk)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def db_list_dialogues_by_scene(db: AsyncSession,
                                     big_scene_id: str = None,
                                     small_scene_id: str = None,
                                     usage: str = None,
                                     npc_id: str = None,):
    """按大场景/小场景/usage 筛选对话，按 dialogue_set 升序。"""
    query = select(Dialogue)
    if big_scene_id is not None:
        query = query.where(Dialogue.big_scene_id == big_scene_id)

    if small_scene_id is not None:
        query = query.where(Dialogue.small_scene_id == small_scene_id)

    if usage is not None:
        query = query.where(Dialogue.usage == usage)

    if npc_id is not None:
        query = query.where(Dialogue.npc == npc_id)

    query = query.order_by(asc(Dialogue.dialogue_set), asc(Dialogue.id))
    result = await db.execute(query)
    return result.scalars().all()
