import os
import json
import random
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from utils import logger
from .agent import ChatAgent

DIALOGUES_PATH = "./resource/dialogues"
SCENES_PATH = "./resource/scenes"
_SCENE_IMAGE_DIR = "./frontend/static/images/scenes"
_SCENE_IMAGE_URL_PREFIX = "/frontend/static/images/scenes"
_IMAGE_EXTS = (".jpg", ".png", ".jpeg", ".webp", ".svg")
_IMMERSIVE_SCENE_OVERRIDE: Dict[str, str] = {"hospital": "clinic"}

# 对话摘要关键词 -> (big_scene_id, small_scene_id)，用于 infer_theme_scene_from_conversation
_SUMMARY_SCENE_KEYWORDS: List[Tuple[str, str, str]] = [
    ("日常", "daily", "home"),
    ("家", "daily", "home"),
    ("home", "daily", "home"),
    ("咖啡", "food", "cafe"),
    ("cafe", "food", "cafe"),
    ("餐厅", "food", "restaurant"),
    ("restaurant", "food", "restaurant"),
    ("机场", "transport", "airport"),
    ("airport", "transport", "airport"),
    ("火车", "transport", "train_station"),
    ("地铁", "transport", "bus_metro"),
    ("出租车", "transport", "taxi"),
    ("taxi", "transport", "taxi"),
    ("酒店", "transport", "hotel"),
    ("hotel", "transport", "hotel"),
    ("超市", "shopping", "supermarket"),
    ("商场", "shopping", "mall"),
    ("理发", "shopping", "barber"),
    ("电影", "shopping", "cinema"),
    ("办公室", "work", "office"),
    ("office", "work", "office"),
    ("面试", "work", "interview"),
    ("会议", "work", "meeting"),
    ("电话", "work", "phone"),
    ("聚会", "social", "party"),
    ("party", "social", "party"),
    ("闲聊", "social", "chat"),
    ("兴趣", "social", "hobby"),
    ("赞美", "social", "praise"),
    ("医院", "daily", "home"),  # clinic 映射到 hospital 小场景
    ("银行", "daily", "bank"),
    ("bank", "daily", "bank"),
]


# 缓存 key
DIALOGUES_CACHE_KEY = "DIALOGUES"
BIG_SCENE_KEY = "BIG_SCENE"
SMALL_SCENE_KEY = "SMALL_SCENE"
SCENE_NPC_CACHE_KEY = "SCENE_NPC"
SCENE_CACHE_TTL = 8 * 3600


async def get_dialogues(db: AsyncSession, agent: ChatAgent) -> List[Dict]:
    """
    从缓存或数据库加载对话列表，返回与 dialogues.json 同结构的 dict 列表（含 big_scene、small_scene、content 为 list）。
    优先读缓存，未命中则通过 crud 查 Dialogue 表并写入缓存。
    """
    data = await agent.cache.get(DIALOGUES_CACHE_KEY)
    if data is not None and isinstance(data, list):
        return data
    try:
        from crud import dialogue as crud_dialogue
        rows = await crud_dialogue.db_list_all_dialogues(db)
        out = [row.to_dict() for row in rows]
        await agent.cache.set(DIALOGUES_CACHE_KEY, out, ttl=SCENE_CACHE_TTL)
        return out
    except Exception as e:
        logger.error(" 从数据库加载 dialogue 数据失败: %s", e)
        return []

async def get_big_scenes(db: AsyncSession, agent: ChatAgent) -> List[Dict]:
    data = await agent.cache.get(BIG_SCENE_KEY)
    if data is not None and isinstance(data, list):
        return data
    try:
        from crud import scene as crud_scene
        rows = await crud_scene.db_list_all_big_scenes(db)
        out = [row.to_dict() for row in rows]
        await agent.cache.set(BIG_SCENE_KEY, out, ttl=SCENE_CACHE_TTL)
        return out
    except Exception as e:
        logger.warning(" 从数据库加载 big_scenes 数据失败: %s", e)
        return []

async def get_small_scenes(db: AsyncSession, agent: ChatAgent) -> List[Dict]:
    data = await agent.cache.get(SMALL_SCENE_KEY)
    if data is not None and isinstance(data, list):
        return data
    try:
        from crud import scene as crud_scene
        rows = await crud_scene.db_list_all_small_scenes(db)
        out = [row.to_dict() for row in rows]
        await agent.cache.set(SMALL_SCENE_KEY, out, ttl=SCENE_CACHE_TTL)
        return out
    except Exception as e:
        logger.warning(" 从数据库加载 small_scenes 数据失败: %s", e)
        return []

def _derive_has_immersive_from_dialogues(dialogues: List[Dict]) -> List[str]:
    """从对话列表中推导有 usage=immersive 的 small_scene_id 去重列表。"""
    return sorted(set(d.get("small_scene_id") for d in dialogues if d.get("usage") == "immersive" and d.get("small_scene_id")))


async def get_scene_npc_data(db: AsyncSession, agent: ChatAgent) -> Optional[Dict[str, Any]]:
    """
    从缓存或 get_dialogues / get_big_scenes / get_small_scenes 组装 scene_npc 结构：has_immersive, big_scenes, small_scenes_by_big。
    不直接访问 Dialogue / BigScene / SmallScene 的 crud。
    """
    data = await agent.cache.get(SCENE_NPC_CACHE_KEY)
    if data is not None and isinstance(data, dict):
        return data
    try:
        big_scenes = await get_big_scenes(db, agent)
        small_rows = await get_small_scenes(db, agent)
        dialogues = await get_dialogues(db, agent)

        small_scenes_by_big: Dict[str, List[Dict]] = {}
        for item in small_rows:
            small_scenes_by_big.setdefault(item.get("big_scene_id"), []).append(item)

        has_immersive = _derive_has_immersive_from_dialogues(dialogues or [])

        out = {
            "has_immersive": has_immersive,
            "big_scenes": big_scenes,
            "small_scenes_by_big": small_scenes_by_big,
        }
        await agent.cache.set(SCENE_NPC_CACHE_KEY, out, ttl=SCENE_CACHE_TTL)
        return out
    except Exception as e:
        logger.warning("get_scene_npc_data 组装失败: %s", e)
        return None


def get_big_scene_image_url(big_scene_id: str):
    """大场景图：文件名 big_{id}.ext，缺省 default_big.svg。"""
    if not big_scene_id:
        return f"{_SCENE_IMAGE_URL_PREFIX}/default_big.svg"

    name = f"big_{big_scene_id}"
    for ext in _IMAGE_EXTS:
        p = os.path.join(_SCENE_IMAGE_DIR, f"{name}{ext}")
        if os.path.isfile(p):
            try:
                mtime = int(os.path.getmtime(p))
                url = f"{_SCENE_IMAGE_URL_PREFIX}/{name}{ext}?t={mtime}"
            except OSError:
                url = f"{_SCENE_IMAGE_URL_PREFIX}/{name}{ext}"
            return url

    return f"{_SCENE_IMAGE_URL_PREFIX}/default_big.svg"

def get_scene_image_url(small_scene_id: str):
    """根据 small_scene_id 返回本地图 URL，无则用 default.svg。带 ?t=mtime 防浏览器强缓存。"""
    if not small_scene_id:
        return f"{_SCENE_IMAGE_URL_PREFIX}/default.svg"

    for ext in _IMAGE_EXTS:
        p = os.path.join(_SCENE_IMAGE_DIR, f"{small_scene_id}{ext}")
        if os.path.isfile(p):
            try:
                mtime = int(os.path.getmtime(p))
                url = f"{_SCENE_IMAGE_URL_PREFIX}/{small_scene_id}{ext}?t={mtime}"
            except OSError:
                url = f"{_SCENE_IMAGE_URL_PREFIX}/{small_scene_id}{ext}"
            return url

    return f"{_SCENE_IMAGE_URL_PREFIX}/default.svg"

def get_npc_image_url(character_id: str) -> str:
    """NPC 图：文件名 npc_{character_id}.ext（character_id 如 home_family），缺省统一使用简单人像 npc_avatar.svg。"""
    if not character_id:
        return f"{_SCENE_IMAGE_URL_PREFIX}/npc_avatar.svg"

    name = f"npc_{character_id}"
    for ext in _IMAGE_EXTS:
        p = os.path.join(_SCENE_IMAGE_DIR, f"{name}{ext}")
        if os.path.isfile(p):
            try:
                mtime = int(os.path.getmtime(p))
                url = f"{_SCENE_IMAGE_URL_PREFIX}/{name}{ext}?t={mtime}"
            except OSError:
                url = f"{_SCENE_IMAGE_URL_PREFIX}/{name}{ext}"
            return url

    return f"{_SCENE_IMAGE_URL_PREFIX}/npc_avatar.svg"


def _derive_small_scenes_by_big(dialogues: List[Dict], big_scene_id: str) -> List[Dict]:
    """从 dialogues 推导某大场景下的小场景"""
    seen = {}
    for d in dialogues:
        if d.get("big_scene_id") != big_scene_id:
            continue
        sid = d.get("small_scene_id")
        if not sid:
            continue
        if sid not in seen:
            seen[sid] = {
                "id": sid,
                "big_scene_id": big_scene_id,
                "name": d.get("small_scene_name", sid),
                "immersive_scene_id": d.get("immersive_scene_id", _IMMERSIVE_SCENE_OVERRIDE.get(sid, sid)),
                "order": len(seen) + 1,
            }
    return sorted(seen.values(), key=lambda x: (x.get("order", 99), x["id"]))


def _derive_npcs_by_small_scene(dialogues: List[Dict], small_scene_id: str) -> List[Dict]:
    """从 dialogues 推导某小场景下的 NPC（仅包含有 learn 对话的）"""
    seen = {}
    for d in dialogues:
        if d.get("small_scene_id") != small_scene_id or d.get("usage") != "learn":
            continue
        nid = d.get("npc")
        if not nid:
            continue
        if nid not in seen:
            seen[nid] = {"id": nid, "small_scene_id": small_scene_id, "name": d.get("npc_name", nid)}
    return list(seen.values())

async def get_big_scenes_with_immersive(agent: ChatAgent, db: Optional[AsyncSession] = None):
    """
    返回带沉浸式的小场景的大场景列表。基于 get_scene_npc_data 或 get_dialogues / get_big_scenes 推导，不直接访问 Dialogue/BigScene/SmallScene crud。
    """
    scene_npc_data = await get_scene_npc_data(db, agent)
    if scene_npc_data:
        has_immersive_set = set(scene_npc_data.get("has_immersive", []))
        small_by_big = scene_npc_data.get("small_scenes_by_big", {})
        result = []
        for b in scene_npc_data.get("big_scenes", []):
            big_id = b.get("id")
            if not big_id:
                continue
            for s in small_by_big.get(big_id) or []:
                if (s.get("small_scene_id") or s.get("id")) in has_immersive_set:
                    result.append({**b, "image": get_big_scene_image_url(big_id)})
                    break
        return result

    dialogues = await get_dialogues(db, agent)
    bigs = await get_big_scenes(db, agent)
    if not isinstance(dialogues, list):
        dialogues = []
    has_immersive_set = set(_derive_has_immersive_from_dialogues(dialogues))
    result = []
    for b in bigs:
        big_id = b.get("id")
        if not big_id:
            continue
        smalls = _derive_small_scenes_by_big(dialogues, big_id)
        for s in smalls:
            if (s.get("id") or "") in has_immersive_set:
                result.append({**b, "image": get_big_scene_image_url(big_id)})
                break
    return result


async def get_big_scenes_with_learn(agent: ChatAgent, db: Optional[AsyncSession] = None) -> List[Dict]:
    """
    返回有 usage=learn 对话的大场景列表，供练习模式自选场景使用。基于 get_dialogues / get_big_scenes 推导。
    """
    dialogues = await get_dialogues(db, agent)
    bigs = await get_big_scenes(db, agent)
    if not dialogues or not bigs:
        return []
    learn_big_ids = set(d.get("big_scene_id") for d in dialogues if d.get("usage") == "learn" and d.get("big_scene_id"))
    result = []
    for b in bigs:
        big_id = b.get("id")
        if big_id and big_id in learn_big_ids:
            result.append({**b, "image": get_big_scene_image_url(big_id)})
    return result


async def get_immersive_small_scenes_by_big(
                                        agent: ChatAgent,
                                        db: Optional[AsyncSession],
                                        big_scene_id: str,
                                        user_id: Optional[int] = None,
                                    ) -> List[Dict]:
    """
    返回某大场景下、有沉浸式对话的小场景列表，每项含 id、small_scene_id、name、image、can_enter 等。
    基于 get_scene_npc_data 或 get_dialogues 推导，不直接访问 Dialogue/BigScene/SmallScene crud。
    """
    scene_npc_data = await get_scene_npc_data(db, agent)
    if scene_npc_data:
        has_immersive_set = set(scene_npc_data.get("has_immersive") or [])
        small_list = (scene_npc_data.get("small_scenes_by_big") or {}).get(big_scene_id) or []
        result = []
        for s in small_list:
            sid = s.get("small_scene_id") or s.get("id")
            if sid and sid in has_immersive_set:
                item = dict(s)
                item["image"] = get_scene_image_url(sid)
                item["title"] = item.get("title") or item.get("name") or sid
                result.append(item)
        await _apply_small_scene_can_enter(db, agent, big_scene_id, result, user_id)
        return result

    dialogues = await get_dialogues(db, agent)
    if not isinstance(dialogues, list):
        dialogues = []
    has_immersive_set = set(_derive_has_immersive_from_dialogues(dialogues))
    smalls = _derive_small_scenes_by_big(dialogues, big_scene_id)
    result = []
    for s in smalls:
        sid = s.get("id")
        if sid and sid in has_immersive_set:
            item = dict(s)
            item["image"] = get_scene_image_url(sid)
            item["title"] = item.get("title") or item.get("name") or sid
            result.append(item)
    await _apply_small_scene_can_enter(db, agent, big_scene_id, result, user_id)
    return result


async def get_unlocked_small_scene_ids(
    db: AsyncSession,
    agent: ChatAgent,
    user_id: int,
) -> List[str]:
    """
    返回当前用户已解锁的小场景 ID 列表。

    定义：在 npc_learn_progress.process 中出现过的 dialogue_id 所属 small_scene_id。
    基于 get_dialogues 与 npc_learn_progress，不直接访问 Dialogue 表。
    """
    from crud import scene_study as crud_study

    row = await crud_study.db_get_npc_learn_progress(db, user_id)
    if not row or not (row.process or "").strip():
        return []

    dialogues = await get_dialogues(db, agent)
    progress = build_progress_from_process(row.process, dialogues or [])
    by_scene = progress.get("by_scene") or {}
    return sorted(by_scene.keys())


async def get_one_immersive_dialogue_for_scene(
    db: AsyncSession,
    agent: ChatAgent,
    small_scene_id: str,
    seed: Optional[str] = None,
) -> Optional[Dict]:
    """
    从 dialogues 中为指定 small_scene_id 挑选一条 usage=immersive 的对话。
    若 seed 不为空，则使用 seed 构造随机种子，保证同一房间两端拿到同一条。
    """
    if not small_scene_id:
        return None
    dialogues = await get_dialogues(db, agent)
    candidates = [
        d
        for d in (dialogues or [])
        if d.get("small_scene_id") == small_scene_id and d.get("usage") == "immersive"
    ]
    if not candidates:
        return None
    if seed:
        rnd = random.Random(str(seed))
        chosen = rnd.choice(candidates)
    else:
        chosen = random.choice(candidates)
    # 返回副本，避免外部修改缓存中的对象
    return dict(chosen)


async def get_one_random_immersive_dialogue(
    db: AsyncSession,
    agent: ChatAgent,
    seed: Optional[str] = None,
) -> Optional[Dict]:
    """
    从所有 dialogues 中随机挑选一条 usage=immersive 的对话。
    seed 存在时用于保证同一房间两端拿到同一条。
    """
    dialogues = await get_dialogues(db, agent)
    candidates = [d for d in (dialogues or []) if d.get("usage") == "immersive"]
    if not candidates:
        return None
    if seed:
        rnd = random.Random(str(seed))
        chosen = rnd.choice(candidates)
    else:
        chosen = random.choice(candidates)
    return dict(chosen)


async def _apply_small_scene_can_enter(
    db: Optional[AsyncSession],
    agent: ChatAgent,
    big_scene_id: str,
    result: List[Dict],
    user_id: Optional[int],
) -> None:
    """
    根据 npc_learn_progress 表为每个小场景设置 can_enter。
    该大场景下 usage=learn 的 dialogue_id 从 get_dialogues 推导，不直接查 Dialogue 表。
    """
    if not result:
        return
    if db is None or user_id is None:
        for item in result:
            item["can_enter"] = False
        return
    from crud import scene_study as crud_study

    row = await crud_study.db_get_npc_learn_progress(db, user_id)
    user_process_set = row.to_process_list() if row else set()

    dialogues = await get_dialogues(db, agent)
    learn_ids_per_small: Dict[str, set] = {}
    for d in (dialogues or []):
        if d.get("usage") != "learn" or d.get("big_scene_id") != big_scene_id:
            continue
        sid = d.get("small_scene_id")
        did = d.get("dialogue_id")
        if sid and did:
            learn_ids_per_small.setdefault(sid, set()).add(did)

    for item in result:
        sid = item.get("small_scene_id") or item.get("id")
        learn_ids = learn_ids_per_small.get(sid, set())
        if not learn_ids:
            item["can_enter"] = True
        else:
            item["can_enter"] = bool(learn_ids & user_process_set)


def build_progress_from_process(process_json: Optional[str],
                                dialogues: List[Dict],
                               ) -> Dict[str, Any]:
    """
    从 NpcLearnProgress.process（dialogue_id 数组的 JSON）与对话列表，构建推荐所需的 progress 结构。
    返回 { "by_scene": { small_scene_id: [npc_id, ...] }, "last_anchor": { "big": "...", "small": "..." } }。
    """
    result_by_scene: Dict[str, List[str]] = {}
    last_anchor: Dict[str, str] = {}
    if not process_json or not process_json.strip():
        return {"by_scene": result_by_scene, "last_anchor": last_anchor}
    try:
        dialogue_ids = json.loads(process_json)
    except json.JSONDecodeError:
        return {"by_scene": result_by_scene, "last_anchor": last_anchor}
    if not isinstance(dialogue_ids, list):
        return {"by_scene": result_by_scene, "last_anchor": last_anchor}

    dialogue_by_id = {d.get("dialogue_id"): d for d in dialogues if d.get("dialogue_id")}
    for did in dialogue_ids:
        if not isinstance(did, str):
            continue
        d = dialogue_by_id.get(did)
        if not d:
            continue
        bid = d.get("big_scene_id")
        sid = d.get("small_scene_id")
        nid = d.get("npc")
        if sid and nid:
            if sid not in result_by_scene:
                result_by_scene[sid] = []
            if nid not in result_by_scene[sid]:
                result_by_scene[sid].append(nid)
        if bid and sid:
            last_anchor = {"big": bid, "small": sid}
    return {"by_scene": result_by_scene, "last_anchor": last_anchor}


def infer_theme_scene_from_conversation(conversation_summary: str) -> Tuple[Optional[str], Optional[str]]:
    """
    从对话摘要推断 (big_scene_id, small_scene_id)，简单关键词匹配。
    """
    if not conversation_summary or not conversation_summary.strip():
        return (None, None)
    summary_lower = conversation_summary.strip().lower()
    for keyword, big_id, small_id in _SUMMARY_SCENE_KEYWORDS:
        if keyword.lower() in summary_lower or keyword in conversation_summary:
            return (big_id, small_id)
    return (None, None)


def get_recommended_anchor_from_history(progress: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    从进度中的 last_anchor 取推荐锚点 (big_scene_id, small_scene_id)。
    """
    la = progress.get("last_anchor") or {}
    return (la.get("big"), la.get("small"))


def get_learn_dialogue(dialogues: List[Dict], small_scene_id: str, npc_id: str) -> Optional[Dict]:
    """取一条 usage=learn 且匹配 small_scene、npc 的对话。"""
    for d in dialogues:
        if (d.get("small_scene_id") == small_scene_id
                and d.get("npc") == npc_id
                and d.get("usage") == "learn"):
            return d
    return None


async def get_dialogue_by_scene_npc_usage(
    db: AsyncSession,
    agent: ChatAgent,
    small_scene_id: str,
    npc_id: str,
    usage: str,
) -> Optional[Dict]:
    """
    按 small_scene_id、npc_id、usage 取单条对话，基于 get_dialogues 过滤，不直接访问 Dialogue 表。
    usage 为 "learn" | "review" | "immersive"。
    """
    dialogues = await get_dialogues(db, agent)
    for d in (dialogues or []):
        if (d.get("small_scene_id") == small_scene_id
                and d.get("npc") == npc_id
                and d.get("usage") == usage):
            out = dict(d)
            out["npc_id"] = out.get("npc") or npc_id
            return out
    return None


def build_card_title(d: Dict) -> str:
    """生成推荐卡片标题，如「家 / 居家 - 家人」。"""
    small_name = (d.get("small_scene_name") or "").strip()
    npc_name = (d.get("npc_name") or "").strip()
    if small_name and npc_name:
        return f"{small_name} - {npc_name}"
    if npc_name:
        return npc_name
    return d.get("dialogue_id") or "英文学习"


async def get_learning_recommendations(
    agent: ChatAgent,
    progress: Dict[str, Any],
    conversation_summary: Optional[str] = None,
    count: int = 4,
    db: Optional[AsyncSession] = None,
) -> List[Dict]:
    """
    获取学习推荐列表：优先从对话摘要推断 1 个主题+场景，否则从进度 last_anchor 取。
    锚点场景推荐该场景下全部 NPC；其余场景每场景随机 1 个。每项含 big_scene_id, small_scene_id, npc_id, npc_name, title, learned。
    dialogues 由外部传入或从缓存/DB 获取（get_dialogues(db, agent)）；若为 None 则先读缓存，有 db 时再读 DB。
    """
    dialogues = await get_dialogues(db, agent)
    if not dialogues:
        return []

    big_scenes = await get_big_scenes(db, agent)
    scene_pairs: List[Tuple[str, str]] = []
    for b in big_scenes:
        bid = b.get("id")
        if not bid:
            continue
        smalls = _derive_small_scenes_by_big(dialogues, bid)
        for s in smalls:
            sid = s.get("id")
            if sid:
                scene_pairs.append((bid, sid))
    if not scene_pairs:
        return []

    by_scene = progress.get("by_scene") or {}

    def learned_set(sid: str) -> set:
        return set(by_scene.get(sid) or [])

    # 1) 锚点：对话推断 或 练习记忆
    anchor_big, anchor_small = (None, None)
    if conversation_summary and conversation_summary.strip():
        anchor_big, anchor_small = infer_theme_scene_from_conversation(conversation_summary)
    if not anchor_big or not anchor_small:
        anchor_big, anchor_small = get_recommended_anchor_from_history(progress)
    if (anchor_big, anchor_small) not in scene_pairs:
        anchor_big, anchor_small = (None, None)

    result: List[Dict] = []
    used_pairs: set = set()

    def add_item_for_npc(bid: str, sid: str, nid: str) -> bool:
        d = get_learn_dialogue(dialogues, sid, nid)
        if not d:
            return False
        title = build_card_title(d)
        npc_name = d.get("npc_name") or nid
        result.append({
            "big_scene_id": bid,
            "small_scene_id": sid,
            "npc_id": nid,
            "npc_name": npc_name,
            "title": title,
            "learned": nid in learned_set(sid),
        })
        return True

    def pick_one_npc_for_scene(sid: str) -> Optional[str]:
        npcs = _derive_npcs_by_small_scene(dialogues, sid)
        if not npcs:
            return None
        learned = learned_set(sid)
        unlearned = [n["id"] for n in npcs if n["id"] not in learned]
        pool = unlearned if unlearned else [n["id"] for n in npcs]
        return random.choice(pool) if pool else None

    def add_one_random_for_scene(bid: str, sid: str) -> bool:
        nid = pick_one_npc_for_scene(sid)
        if not nid:
            return False
        used_pairs.add((bid, sid))
        return add_item_for_npc(bid, sid, nid)

    # 2) 锚点场景：该场景下全部 NPC 各推荐一条（带 learned 标识）
    if anchor_big and anchor_small:
        used_pairs.add((anchor_big, anchor_small))
        npcs = _derive_npcs_by_small_scene(dialogues, anchor_small)
        for n in npcs:
            nid = n.get("id")
            if nid:
                add_item_for_npc(anchor_big, anchor_small, nid)

    # 3) 其余场景：每场景随机 1 个，直到达到 count
    remaining = [(b, s) for (b, s) in scene_pairs if (b, s) not in used_pairs]
    random.shuffle(remaining)
    for (bid, sid) in remaining:
        if len(result) >= count:
            break
        add_one_random_for_scene(bid, sid)

    return result
