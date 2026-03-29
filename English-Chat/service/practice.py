"""
练习模式：对话解析、轮次与下一句计算，供 /api/practice/* 使用。
"""
import json
from typing import Optional, List, Dict, Any, Tuple

def get_first_turn_for_start(dialogue_lines: List[Dict]) -> Tuple[str, Optional[str], Dict[str, Any], int]:
    # 获取第一句台词。规则：A=NPC，B=用户。可能以A或B开始
    first_a_text = None
    first_a_audio_url = None
    first_b_text = None
    first_b_line = {}
    if dialogue_lines[0]["speaker"] == "A":
        first_a_text = dialogue_lines[0]["text"]
        first_a_audio_url = dialogue_lines[0].get("audio_url")
        if len(dialogue_lines) > 1 and dialogue_lines[1]["speaker"] == "B":
            first_b_text = dialogue_lines[1]["text"]
            first_b_line = dialogue_lines[1]
    else:
        # 以B开始：用户先说第一句
        first_b_text = dialogue_lines[0]["text"]
        first_b_line = dialogue_lines[0]

    # 如果有B的台词，取提示：优先用口语库的 hint（须含关键词/关键句），否则 AI 抽取
    hints = None
    if first_b_text:
        if first_b_line.get("hint"):
            h = first_b_line["hint"]
            phrases = [x.strip() for x in h.split("/") if x.strip()]
            # 若 hint 像动作描述（如 ask address）无具体可说内容，用本句 content 作参考句
            if len(phrases) == 1 and phrases[0].islower() and "?" not in phrases[0] and len(phrases[0]) < 30:
                phrases.append(first_b_text)
            hints = {"phrases": phrases, "pattern": "", "words": [], "grammar": "", "key_sentence": first_b_text}
        else:
            hints = {"phrases": [first_b_text], "pattern": "", "words": [], "grammar": "", "key_sentence": first_b_text}

    total_turns = len([l for l in dialogue_lines if l["speaker"] == "B"])
    return first_a_text, first_a_audio_url, hints, total_turns


def get_reference_b_line(dialogue_lines: List[Dict], current_turn: int) -> Optional[Dict]:
    """返回第 current_turn 条 B 行（0-based），无则返回 None。"""
    b_index = 0
    for line in dialogue_lines:
        if (line.get("speaker") or "A")[:1].upper() == "B":
            if b_index == current_turn:
                return line
            b_index += 1
    return None


def get_next_after_turn(
    dialogue_lines: List[Dict], current_turn: int
) -> Tuple[str, Optional[str], Dict[str, Any], int, bool]:
    """
    用户完成第 current_turn 轮 B 后，返回下一句 A 的 text、audio_url，下一句 B 的 hints，
    以及 next_turn 和 is_completed。
    若最后一句是 A 说的，用户说完倒数第二句后仍有下一句 A 要展示，此时 is_completed=False，
    前端先展示/播放该句 A，再根据 complete_after_this_a 或“无下一句 B”进入结束流程。
    """
    next_a_text = ""
    next_a_audio_url = None
    next_b_hints: Dict[str, Any] = {"phrases": [], "key_sentence": ""}
    next_turn = current_turn + 1
    is_completed = True
    b_index = 0
    for i, line in enumerate(dialogue_lines):
        sp = (line.get("speaker") or "A")[:1].upper()
        if sp == "B":
            if b_index == current_turn:
                j = i + 1
                while j < len(dialogue_lines):
                    if (dialogue_lines[j].get("speaker") or "A")[:1].upper() == "A":
                        lj = dialogue_lines[j]
                        next_a_text = lj.get("text") or lj.get("content") or ""
                        next_a_audio_url = lj.get("audio_url")
                        j += 1
                        if j < len(dialogue_lines) and (dialogue_lines[j].get("speaker") or "A")[:1].upper() == "B":
                            nb = dialogue_lines[j]
                            # 提示构造逻辑与首轮保持一致：
                            # - 若 hint 有内容：按「/」拆成多个关键词/短语；
                            # - 若 hint 看起来像动作描述（全小写、无问号且较短），则追加整句文本作为参考句；
                            # - 若 hint 为空，则用当前 B 句文本作为参考句与默认“关键词”。
                            raw_hint = nb.get("hint") or ""
                            key_sentence = nb.get("text") or nb.get("content") or raw_hint or ""
                            phrases: List[str] = []
                            if raw_hint:
                                phrases = [x.strip() for x in raw_hint.split("/") if x.strip()]
                                if (
                                    len(phrases) == 1
                                    and phrases[0].islower()
                                    and "?" not in phrases[0]
                                    and len(phrases[0]) < 30
                                ):
                                    # hint 像「ask address」这类动作描述时，把整句文本也作为可见提示
                                    if key_sentence and key_sentence not in phrases:
                                        phrases.append(key_sentence)
                            elif key_sentence:
                                phrases = [key_sentence]

                            next_b_hints = {
                                "phrases": phrases,
                                "key_sentence": key_sentence,
                            }
                            is_completed = False
                        else:
                            # 还有一句 A 要展示（最后一句是 AI），先不标记完成，让前端先展示这句
                            if next_a_text:
                                is_completed = False
                        break
                    j += 1
                break
            b_index += 1
    return next_a_text, next_a_audio_url, next_b_hints, next_turn, is_completed
