import os
from datetime import datetime, timedelta

import json

from config import configer

ENGLISH_LEVELS = {
    "minimal": {
        "name": "极简",
        "description": "极简级，最简单的日常用语，适合2句话对话",
        "difficulty": {
            "vocabulary": "最基础词汇（500词以内），如 hello, thank you, yes, no, how are you",
            "vocab_scope": "只使用超高频生活用词，避免抽象或学术词",
            "vocab_avoid": "避免多音节或罕见词（如 sophisticated, comprehensive）",
            "grammar": "仅现在时，最简单的陈述句和疑问句",
            "grammar_structures": "只用主谓或主谓宾；不使用从句",
            "tenses": ["present simple"],
            "idioms": False,
            "idiom_ratio": "0%",
            "slang": False,
            "sentence_length": "3-6词",
            "sentence_length_range": "3-6词",
            "complexity": "最简单的短句，主谓结构",
            "info_density": "每句只表达1个信息点"
        }
    },
    "beginner": {
        "name": "初级（A1）",
        "description": "入门级，基础词汇和简单句型",
        "difficulty": {
            "vocabulary": "基础词汇（1000词以内）",
            "vocab_scope": "高频日常用词，避免抽象名词和复杂动词",
            "vocab_avoid": "避免高阶词（如 elaborate, nuanced）",
            "grammar": "现在时、简单过去时、基本疑问句",
            "grammar_structures": "主谓宾为主，允许简单并列句",
            "tenses": ["present simple", "past simple"],
            "idioms": False,
            "idiom_ratio": "0-5%",
            "slang": False,
            "sentence_length": "5-8词",
            "sentence_length_range": "5-8词",
            "complexity": "简单句，主谓宾结构",
            "info_density": "每句1个信息点，避免多层信息"
        }
    },
    "elementary": {
        "name": "基础（A2）",
        "description": "基础级，日常交流词汇",
        "difficulty": {
            "vocabulary": "日常词汇（2000词以内）",
            "vocab_scope": "日常场景词汇为主，可少量加入生活短语",
            "vocab_avoid": "避免学术词或专业术语",
            "grammar": "现在时、过去时、将来时、现在进行时",
            "grammar_structures": "简单并列句，允许because/and连接",
            "tenses": ["present simple", "past simple", "future simple", "present continuous"],
            "idioms": "少量常见习语（如 'how are you', 'nice to meet you'）",
            "idiom_ratio": "5-10%",
            "slang": False,
            "sentence_length": "8-12词",
            "sentence_length_range": "8-12词",
            "complexity": "简单句和并列句",
            "info_density": "每句1-2个信息点"
        }
    },
    "pre_intermediate": {
        "name": "准中级（A2-B1）",
        "description": "准中级，开始使用复合句",
        "difficulty": {
            "vocabulary": "扩展词汇（3000词以内）",
            "vocab_scope": "生活与学习场景常用词，允许适度抽象词",
            "vocab_avoid": "避免罕见学术词或文学词",
            "grammar": "所有基本时态、条件句、被动语态",
            "grammar_structures": "允许1个从句（because/when/if）",
            "tenses": ["all basic tenses", "present perfect", "past continuous", "conditional"],
            "idioms": "常见习语和短语动词",
            "idiom_ratio": "10-15%",
            "slang": "少量日常俚语",
            "sentence_length": "10-15词",
            "sentence_length_range": "10-15词",
            "complexity": "复合句，从句",
            "info_density": "每句1-2个信息点，允许补充细节"
        }
    },
    "intermediate": {
        "name": "中级（B1-B2）",
        "description": "中级，流利日常交流",
        "difficulty": {
            "vocabulary": "丰富词汇（5000词以内）",
            "vocab_scope": "常用进阶词+语境化表达",
            "vocab_avoid": "避免过度书面或极少见词汇",
            "grammar": "所有时态、虚拟语气、复杂语法结构",
            "grammar_structures": "允许2个从句或非限定性从句",
            "tenses": ["all tenses", "present perfect continuous", "past perfect", "subjunctive"],
            "idioms": "常用习语和表达",
            "idiom_ratio": "15-20%",
            "slang": "日常俚语和口语表达",
            "sentence_length": "12-18词",
            "sentence_length_range": "12-18词",
            "complexity": "复杂复合句，多种从句",
            "info_density": "每句2个信息点，允许对比或解释"
        }
    },
    "upper_intermediate": {
        "name": "中高级（B2）",
        "description": "中高级，复杂话题讨论",
        "difficulty": {
            "vocabulary": "高级词汇（8000词以内）",
            "vocab_scope": "进阶与抽象表达，含部分领域词汇",
            "vocab_avoid": "避免生僻学术词堆砌",
            "grammar": "所有语法结构，包括倒装、强调句",
            "grammar_structures": "允许多重从句与强调结构",
            "tenses": ["all tenses including perfect continuous forms"],
            "idioms": "丰富习语和地道表达",
            "idiom_ratio": "20-25%",
            "slang": "常见俚语和流行语",
            "sentence_length": "15-22词",
            "sentence_length_range": "15-22词",
            "complexity": "复杂句式，多种语法结构混合",
            "info_density": "每句2-3个信息点"
        }
    },
    "advanced": {
        "name": "高级（B2-C1）",
        "description": "高级，接近母语水平",
        "difficulty": {
            "vocabulary": "高级词汇和学术词汇（10000+词）",
            "vocab_scope": "高级抽象表达+部分学术用语",
            "vocab_avoid": "避免极端冷僻或专业术语堆叠",
            "grammar": "所有高级语法，包括修辞手法",
            "grammar_structures": "允许复杂从句、倒装、强调与修辞",
            "tenses": ["all tenses with nuanced usage"],
            "idioms": "大量习语、谚语和地道表达",
            "idiom_ratio": "25-30%",
            "slang": "丰富俚语、网络用语和流行语",
            "sentence_length": "18-25词",
            "sentence_length_range": "18-25词",
            "complexity": "复杂句式，多种修辞手法",
            "info_density": "每句2-3个信息点，允许抽象表达"
        }
    }
}

LEARN_STAGE_DESC = {
    "chinese_chat": """
【重要：回复风格要求】
- 你只用中文回复，且必须使用中文专用表达（本阶段不涉及英文）。
- 引导用户说出兴趣、爱好、学英语目的、偏好，以及想学习什么对话场景（如：餐厅点餐、机场、酒店、办公室等）。
- 每次只问一件事或只做一句确认，回复控制在 20 字以内。
- 用户说想练哪个场景就确认哪个场景；若用户说"开始学英语"、"开始英文学习"等，表示要进入英文学习阶段。
""",
    "english_learning":
"""
【重要：回复风格要求】
- 你必须用英文回复用户
- 根据用户的英文水平（{level_display}）调整回复难度
- 基于用户的兴趣、职业和今天的对话内容进行教学
- 回复要简洁，控制在50-100字
- 可以纠正用户的语法错误，但要友好
""",
    "daily_chat":
"""
【重要：回复风格要求】
- 回复要像正常朋友聊天一样，简洁自然
- 若当前为中文沟通阶段：每次回复控制在 20 字以内，只做场景确认，不啰嗦
- 若为英文学习阶段：每次回复控制在 30-80 字左右（2-3 句话）
- 不要使用过多的比喻、修饰词或诗意语言，直接回答问题，不要绕弯子
- 除非用户明确要求详细解释，否则保持简短
- 这个要求优先于所有其他风格要求
"""
}


def get_time_prompt() -> str:
    today = datetime.now()
    today_str = today.strftime("%Y年%m月%d日")
    today_iso = today.strftime("%Y-%m-%d")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]

    context_parts = [f"[当前时间信息]\n今天是{today_str}（{weekday}），日期：{today_iso}"]

    context = "\n\n".join(context_parts)
    context += f"""
请根据以上信息与用户对话：
1. 明确知道今天是{today_str}
2. 如果用户提到"昨天"、"今天"、"明天"，要能准确理解
4. 回复要简洁自然，像正常朋友聊天一样。每次回复尽量控制在50-100字左右，除非用户明确要求详细解释。
"""
    return context

def get_user_profile_prompt(user_profile: dict) -> str:
    context_parts = []

    if user_profile.get("name"):
        context_parts.append(f"姓名：{user_profile['name']}")
    if user_profile.get("age"):
        context_parts.append(f"年龄：{user_profile['age']}")
    if user_profile.get("occupation"):
        context_parts.append(f"职业：{user_profile['occupation']}")
    if user_profile.get("interests"):
        val = user_profile["interests"]
        interests = ", ".join(val) if isinstance(val, list) else str(val)
        context_parts.append(f"兴趣：{interests}")
    if user_profile.get("preferences"):
        val = user_profile["preferences"]
        prefs = ", ".join(val) if isinstance(val, list) else str(val)
        context_parts.append(f"偏好：{prefs}")
    if user_profile.get("goals"):
        val = user_profile["goals"]
        goals = ", ".join(val) if isinstance(val, list) else str(val)
        context_parts.append(f"目标：{goals}")
    if user_profile.get("habits"):
        val = user_profile["habits"]
        habits = ", ".join(val) if isinstance(val, list) else str(val)
        context_parts.append(f"习惯：{habits}")

    # 添加英文水平信息
    if user_profile.get("english_level"):
        level_key = user_profile["english_level"]
        level_config = ENGLISH_LEVELS.get(level_key)
        if level_config:
            level_display = f"{level_config['name']} - {level_config['description']}"
        else:
            level_display = level_key
        context_parts.append(f"英文水平：{level_display}")

    if context_parts:
        return "[用户档案信息]\n" + "\n".join(context_parts)
    return ""

def get_study_prompt(learning_stage, user_profile: dict) -> str:
    context = ""
    if learning_stage == "english_learning":
        # 英文学习阶段
        english_level = user_profile.get("english_level", "beginner")

        level_map = {
            "beginner": "初级（A1-A2）",
            "elementary": "基础（A2-B1）",
            "intermediate": "中级（B1-B2）",
            "advanced": "高级（B2-C1）"
        }
        level_display = level_map.get(english_level, "初级")
        context += format(LEARN_STAGE_DESC.get(learning_stage, ""))
    else:
        context += LEARN_STAGE_DESC.get(learning_stage, "")

    return context

def adjust_prompt(mood, character):
    """Load mood-specific prompts from the character's prompts.json file. 按用户分状态可传 account_name。"""
    character_prompts_path = os.path.join(configer.characters_folder, character, 'prompts.json')
    try:
        # Try to load character-specific prompts
        if os.path.exists(character_prompts_path):
            with open(character_prompts_path, 'r', encoding='utf-8') as f:
                mood_prompts = json.load(f)
        else:
            # Fall back to global prompts
            prompts_path = os.path.join(configer.characters_folder, 'prompts.json')
            with open(prompts_path, 'r', encoding='utf-8') as f:
                mood_prompts = json.load(f)
    except FileNotFoundError:
        print(f"Error loading prompts: character or global prompts.json not found. Using default prompts.")
        mood_prompts = {
            "happy": "RESPOND WITH JOY AND ENTHUSIASM.",
            "sad": "RESPOND WITH KINDNESS AND COMFORT.",
            "flirty": "RESPOND WITH A TOUCH OF MYSTERY AND CHARM.",
            "angry": "RESPOND CALMLY AND WISELY.",
            "neutral": "KEEP RESPONSES SHORT AND NATURAL.",
            "fearful": "RESPOND WITH REASSURANCE.",
            "surprised": "RESPOND WITH AMAZEMENT.",
            "disgusted": "RESPOND WITH UNDERSTANDING.",
            "joyful": "RESPOND WITH EXUBERANCE."
        }
    except Exception as e:
        print(f"Error loading prompts: {e}")
        mood_prompts = {}

    # Get the mood prompt but don't print it in normal logging
    mood_prompt = mood_prompts.get(mood, "")

    return "\n【回复语气要求: 】\n" + mood_prompt + "\n回复中不要省略标点符号"

def extrac_user_profile(conversation_text: str):
    extract_prompt = f"""请从以下对话中提取用户明确提到的关键信息，以JSON格式返回。

    重要要求：
    1. 只提取对话中明确提到的信息，不要推断或添加细节
    2. 如果用户说"我叫张磊"，提取name为"张磊"
    3. 如果用户说"我喜欢篮球和电影"，提取interests为["篮球", "电影"]
    4. 如果信息不明确或未提到，使用null或空数组/对象

    对话内容：
    {conversation_text}

    请提取以下信息（如果对话中明确提到）：
    1. 姓名（name）
    2. 年龄（age）
    3. 职业（occupation）
    4. 兴趣（interests）
    5. 偏好（preferences，如语言偏好、学习方式等）
    6. 目标（goals）
    7. 习惯（habits）
    8. 其他重要信息（other_info）

    返回格式（JSON）：
    {{
        "name": "用户姓名或null",
        "age": "年龄或null",
        "occupation": "职业或null",
        "interests": "兴趣1, 兴趣2 或者null",
        "preferences": "偏好或者null",
        "goals": "目标或者null",
        "habits": "习惯或者null",
        "other_info": "其他信息或者null"
    }}

    只返回JSON，不要其他说明。如果某项信息不存在，使用null。"""

    return extract_prompt


def get_practice_respond_validation_system_prompt(user_input: str, reference_text: str) -> str:
    """练习模式用户回复校验：LLM 系统提示词，要求只输出 JSON 判断用户回复与参考句是否意思一致。"""
    prompt = f"""判断以下两个英文句子的意思是否一致。

参考句子：{reference_text}
用户输入：{user_input}

要求：
1. 如果意思一致或部分一致（即使表达不同），返回 "consistent"
2. 如果用户输入明显偏离主题或完全无关（瞎说），返回 "inconsistent"
3. 如果用户输入为空或几乎没有内容（不说）或者说中文，返回 "inconsistent"
4. 如果用户输入有明显语法错误但不影响理解，返回 "consistent_with_errors"

注意：只要意思相关，即使表达方式不同，也应该返回 "consistent"。

只返回JSON格式，不要其他说明：
例如： 
{{"result": "inconsistent", "reason": "对话偏离主题"}}"""

    return prompt

def get_immersive_chat_system_prompt(
    npc_name: str,
    user_goal: str = "",
    role_swapped: bool = False,
    reference_script: str = "",
) -> str:
    """沉浸式自由对话：系统提示包含该 NPC 的 immersive 对话全部内容；对话主题须与原对话一致，偏离时引导回主题，必须纯英文回复。"""
    # 互换角色后，必须明确“你是谁 / 用户是谁”，避免模型被参考剧本或 NPC 名称误导。
    if role_swapped:
        identity_block = (
            f"你在这个场景中扮演【学习者/顾客】（不要扮演 {npc_name}）。"
            f"用户扮演【NPC/服务员等场景角色】（{npc_name}）。"
        )
        goal_block = f"你的目标（学习者/顾客要完成的对话目标）：{user_goal}" if user_goal else "你的目标：自然推进场景对话并完成该场景的对话任务。"
    else:
        identity_block = (
            f"你在这个场景中扮演【NPC/服务员等场景角色】（{npc_name}）。"
            "用户扮演【学习者/顾客】。"
        )
        goal_block = f"用户的目标（学习者/顾客要完成的对话目标）：{user_goal}" if user_goal else "用户的目标：自然推进场景对话并完成该场景的对话任务。"

    script_block = (
        f"\n【参考剧本（包含双方台词；主题必须与此一致，不必逐字复述）】\n{reference_script}"
        if reference_script
        else ""
    )

    json_format_block = (
        "\n【输出格式（非常重要）】\n"
        "你必须严格输出一个 JSON 对象，键名固定为 reply 和 hints，例如：\n"
        '{\"reply\": \"Your English line(s) here.\", \"hints\": [\"Hint 1.\", \"Hint 2.\", \"Hint 3.\"]}\n'
        "规则：\n"
        "- reply：只包含你要说给用户听的英文台词（1-3 句话），不要包含 'reply:'、不要包含任何中文、不要包含解释；\n"
        "- hints：给用户的 2-3 条英文提示句（告诉用户下一句可以怎么说），用数组；\n"
        "- 只输出 JSON，不要输出代码块标记或多余说明。\n"
    )

    return (
        identity_block
        + "\n你必须用纯英文回复，保持角色一致、简洁自然（1-3 句话）。\n"
        + goal_block
        + script_block
        + "\n对话主题必须与参考剧本一致；若用户发言偏离主题，请用英文委婉引导用户回到该主题。\n"
        + json_format_block
    )


def get_immersive_report_system_prompt() -> str:
    """沉浸式对话报告：生成包含「重点单词」「万能句型」「错误修正」的 Markdown 复习资料。"""
    return """你是英语学习助手。根据「本场对话主题」「参考剧本」和「用户对话记录」，生成一份用于复习的 Markdown 报告。

报告必须包含且仅包含以下三个部分（用二级标题，顺序不可调换），标题文本要与下面完全一致：

1. ## 重点单词
   - 从本场对话中挑选 3～8 个**最值得记忆的词或短语**（包括对话中真实出现的，以及非常贴合本场景的高价值表达）。
   - 使用无序列表，每条一行，格式建议为：
     - 英文单词/短语 — 简短中文释义或使用提示（可以加上时态/搭配等关键信息）。

2. ## 万能句型
   - 提取 3～6 条在**本场景及相似场景都很常用的英文句子**，适合作为“背下来就能直接套用”的句型。
   - 使用无序列表，每条一行，格式建议为：
     - 英文句子 — 简短中文说明（适用场景/语气特点等）。

3. ## 错误修正
   - 针对用户在本场对话中的英语表达，如有问题，请逐条给出“原句 → 建议句”的纠正列表。
   - 使用无序列表，每条一行，格式建议为：
     - 用户说：原句 → 建议：正确表达（括号里用简短中文说明，是语法问题、用词问题还是发音/拼写问题）。
   - 若本场对话中**没有明显错误**，写一条列表项，例如：
     - 表达整体正确，暂未发现需要重点纠正的问题，可以继续保持当前的表达方式。

统一要求：
- 只输出 Markdown 文本，不要输出 JSON、代码块标记或多余解释。
- 严格使用上面给出的三个二级标题，并按顺序输出。
- 各部分内部内容使用清晰的无序列表（每条一行），方便在前端按条目展示。"""


def get_immersive_report_message(
    transcript: list,
    reference_script: str = "",
    dialogue_topic: str = "",
) -> str:
    """沉浸式报告：将对话主题、参考剧本与用户对话记录拼成 LLM 用户消息。"""
    lines = []
    if dialogue_topic:
        lines.append("【本场对话主题】")
        lines.append(dialogue_topic)
        lines.append("")
    if reference_script:
        lines.append("【参考剧本】")
        lines.append(reference_script)
        lines.append("")
    lines.append("【用户对话记录】")
    for i, item in enumerate(transcript or [], 1):
        role = (item.get("role") or "user").lower()
        content = (item.get("content") or "").strip()
        lines.append(f"{i}. [{role}] {content}")
    return "\n".join(lines)

def get_practice_generate_review_corrections_message(user_inputs: list, dialogue_topic: str) -> str:
    lines = []
    for item in (user_inputs or []):
        if not isinstance(item, dict):
            continue
        turn = item.get("turn")
        ai_said = (item.get("ai_said") or "").strip()
        user_said = (item.get("user_said") or "").strip()
        reference = (item.get("reference") or "").strip()
        order = (item.get("order") or "").strip().upper()
        # 默认：若未提供 order，则按常见场景（用户 B 先说）展示为 用户在前、AI 在后
        if order == "AB":
            lines.append(f"轮次 {turn}: 参考: {reference} | AI: {ai_said} | 用户: {user_said}")
        else:
            lines.append(f"轮次 {turn}: 参考: {reference} | 用户: {user_said} | AI: {ai_said}")
    user_inputs_text = "\n".join(lines)
    prompt = f"""根据练习会话对用户说的内容做口语纠错（发音/语法），忽略大小写和标点。对话主题：{dialogue_topic}

规则（重要）：
- 只针对「用户」发言给出纠错与更自然/更完整的说法。
- 若用户发言明显过短或不完整（例如只说“please / yes / ok”等），即使没有语法错误，也应结合该轮「参考」句给出建议表达（把参考句作为 correct）。
- 若用户发言和参考句意思一致但表达不完整，给出更完整的口语表达（可直接使用参考句或对参考句做轻微口语化）。

会话：
{user_inputs_text}

【必须】只输出一行完整 JSON，从 {{ 开始到 }} 结束，不要只输出 "corrections:" 后截断。格式：{{"corrections":[{{"user_said":"原句","correct":"正确表达","explanation":"简要说明"}}]}}。无错误可输出：{{"corrections":[]}}"""
    return prompt