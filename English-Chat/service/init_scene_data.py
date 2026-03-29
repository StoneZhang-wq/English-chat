"""
系统启动时：从 JSON 文件同步数据到 BigScene、SmallScene、Dialogue 表。
规则：对比主键，主键已存在则忽略，不存在则插入（仅增量插入新数据）。
加载顺序：BigScene -> SmallScene -> Dialogue（满足外键依赖）。
"""
import os
import json
from typing import Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.scene import BigScene, SmallScene
from models.dialogue import Dialogue
from utils import logger

DIALOGUES_PATH = "./resource/dialogues"
SCENES_PATH = "./resource/scenes"


async def _existing_big_scene_ids(session: AsyncSession) -> Set[str]:
    """返回 BigScene 表中已存在的主键 id 集合。"""
    result = await session.execute(select(BigScene.id))
    return set(row[0] for row in result.fetchall())


async def _existing_small_scene_ids(session: AsyncSession) -> Set[str]:
    """返回 SmallScene 表中已存在的主键 id 集合。"""
    result = await session.execute(select(SmallScene.id))
    return set(row[0] for row in result.fetchall())


async def _existing_dialogue_ids(session: AsyncSession) -> Set[str]:
    """返回 Dialogue 表中已存在的 dialogue_id 集合（业务主键）。"""
    result = await session.execute(select(Dialogue.dialogue_id))
    return set(row[0] for row in result.fetchall())


async def load_big_scenes_from_json(session: AsyncSession, filepath: str) -> int:
    """从 scene_npc_index.json 的 big_scenes 写入 BigScene 表；主键已存在则忽略，否则插入。返回本次插入条数。"""
    if not os.path.isfile(filepath):
        logger.warning("init_scene_data: 文件不存在 %s", filepath)
        return 0
    existing = await _existing_big_scene_ids(session)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    bigs = data.get("big_scenes") or []
    count = 0
    for b in bigs:
        bid = b.get("id")
        if not bid or bid in existing:
            continue
        existing.add(bid)
        name = b.get("name") or bid
        order = int(b.get("order", 99))
        session.add(BigScene(id=bid, name=name, sort_order=order))
        count += 1
    if count:
        await session.flush()
    return count


async def load_small_scenes_from_json(session: AsyncSession, filepath: str) -> int:
    """从 scene_npc_index.json 的 small_scenes_by_big 写入 SmallScene 表；主键已存在则忽略，否则插入。依赖 BigScene 已存在。"""
    if not os.path.isfile(filepath):
        logger.warning("init_scene_data: 文件不存在 %s", filepath)
        return 0
    existing = await _existing_small_scene_ids(session)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    small_by_big = data.get("small_scenes_by_big") or {}
    count = 0
    seen_small_ids = set()
    for big_id, items in small_by_big.items():
        if not items:
            continue
        for s in items:
            sid = s.get("small_scene_id") or s.get("id")
            if not sid or sid in seen_small_ids or sid in existing:
                continue
            seen_small_ids.add(sid)
            existing.add(sid)
            name = s.get("name") or sid
            immersive = s.get("immersive_scene_id") or s.get("id") or sid
            order = int(s.get("order", 0))
            session.add(SmallScene(
                id=sid,
                big_scene_id=big_id,
                name=name,
                immersive_scene_id=immersive,
                sort_order=order,
            ))
            count += 1
    if count:
        await session.flush()
    return count


async def load_dialogues_from_json(session: AsyncSession, filepath: str) -> int:
    """从 dialogues.json 写入 Dialogue 表；dialogue_id 已存在则忽略，否则插入。依赖 BigScene、SmallScene 已存在。"""
    if not os.path.isfile(filepath):
        logger.warning("init_scene_data: 文件不存在 %s", filepath)
        return 0
    existing = await _existing_dialogue_ids(session)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return 0
    count = 0
    for d in data:
        dialogue_id = d.get("dialogue_id")
        if not dialogue_id or dialogue_id in existing:
            continue
        existing.add(dialogue_id)
        big_id = d.get("big_scene")
        small_id = d.get("small_scene")
        if not big_id or not small_id:
            continue
        content = d.get("content")
        if isinstance(content, list):
            content = json.dumps(content, ensure_ascii=False)
        elif not isinstance(content, str):
            content = "[]"
        session.add(Dialogue(
            dialogue_id=dialogue_id,
            big_scene_id=big_id,
            small_scene_id=small_id,
            npc=d.get("npc") or "",
            dialogue_set=int(d.get("dialogue_set", 1)),
            usage=d.get("usage") or "learn",
            content=content,
            core_sentences=d.get("core_sentences"),
            core_chunks=d.get("core_chunks"),
            big_scene_name=d.get("big_scene_name"),
            small_scene_name=d.get("small_scene_name"),
            npc_name=d.get("npc_name"),
            user_goal=d.get("user_goal"),
            user_goal_a=d.get("user_goal_a"),
        ))
        count += 1
    if count:
        await session.flush()
    return count


async def load_data_from_json(session: AsyncSession) -> None:
    """
    从 JSON 同步到数据库：按 BigScene -> SmallScene -> Dialogue 顺序执行。
    每条 JSON 数据与库中主键对比，主键一致则忽略，不一致则插入（仅插入新数据）。
    """
    scene_index_path = os.path.join(SCENES_PATH, "scene_npc_index.json")
    dialogues_path = os.path.join(DIALOGUES_PATH, "dialogues.json")

    try:
        c_big = await load_big_scenes_from_json(session, scene_index_path)
        logger.info("init_scene_data: BigScene 本次插入 %d 条（主键已存在已忽略）", c_big)

        c_small = await load_small_scenes_from_json(session, scene_index_path)
        logger.info("init_scene_data: SmallScene 本次插入 %d 条（主键已存在已忽略）", c_small)

        c_dialogue = await load_dialogues_from_json(session, dialogues_path)
        logger.info("init_scene_data: Dialogue 本次插入 %d 条（dialogue_id 已存在已忽略）", c_dialogue)

        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception("init_scene_data 失败: %s", e)
        raise
