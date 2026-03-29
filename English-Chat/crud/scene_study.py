import json
from typing import List

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Index, Integer, String, Enum, DateTime, ForeignKey
from models.scene_npc import NpcLearnProgress


async def db_get_npc_learn_progress(db: AsyncSession, user_id: int):
    """按用户查询学习进度，无则返回 None。"""
    query = select(NpcLearnProgress).where(NpcLearnProgress.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def db_update_npc_process(db: AsyncSession, user_id: int, process_json: str):
    """更新用户学习进度：process 为 JSON 数组字符串 [dialogue_id, ...]；无记录则先创建。"""
    row = await db_get_npc_learn_progress(db, user_id)
    if row:
        stmt = update(NpcLearnProgress).where(NpcLearnProgress.user_id == user_id).values(process=process_json)
        await db.execute(stmt)
    else:
        row = NpcLearnProgress(user_id=user_id, process=process_json)
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def db_create_or_update_npc_learn_progress(db: AsyncSession, user_id: int, process_json: str):
    """创建或更新学习进度（process 为 dialogue_id 数组的 JSON 字符串）。"""
    return await db_update_npc_process(db, user_id, process_json)


async def db_delete_npc_learn_progress(db: AsyncSession, user_id: int):
    """删除指定用户的学习进度。"""
    stmt = delete(NpcLearnProgress).where(NpcLearnProgress.user_id == user_id)
    await db.execute(stmt)
    await db.commit()


async def db_append_dialogue_ids_to_process(
    db: AsyncSession, user_id: int, dialogue_ids: List[str]
) -> List[str]:
    """
    将 dialogue_id 列表并入该用户的 process 字段（JSON 数组），去重并保持顺序。
    返回合并后的完整 dialogue_id 列表。
    """
    if not dialogue_ids:
        dialogue_ids = []
    seen = set()
    new_ids = [x for x in dialogue_ids if isinstance(x, str) and x.strip() and x not in seen and not seen.add(x)]
    row = await db_get_npc_learn_progress(db, user_id)
    existing = []
    if row and row.process and row.process.strip():
        try:
            parsed = json.loads(row.process)
            if isinstance(parsed, list):
                existing = [x for x in parsed if isinstance(x, str) and x.strip()]
        except (TypeError, json.JSONDecodeError):
            pass
    merged = list(existing)
    for did in new_ids:
        if did not in merged:
            merged.append(did)
    process_json = json.dumps(merged, ensure_ascii=False)
    await db_update_npc_process(db, user_id, process_json)
    return merged
