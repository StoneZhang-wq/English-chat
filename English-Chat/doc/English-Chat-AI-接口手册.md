
# English-Chat-AI 项目接口手册

## 一、项目概述

English-Chat-AI 是一个英语口语AI练习系统，支持语音对话、文字聊天、场景模拟、1v1真人练习等功能。
后端基于 FastAPI，前端使用原生 JavaScript。

### 技术栈
- 后端: FastAPI (Python)
- 前端: Vanilla JavaScript + WebSocket
- AI: OpenAI / 豆包 (LLM + TTS + ASR)
- 数据库: Supabase (用户数据/记忆)

---

## 二、基础信息

### 2.1 API 基础URL
```
http://localhost:8000
```

### 2.2 认证方式
- 用户账号: 通过 `/api/account/login` 登录获取会话
- WebSocket: 通过 `X-Account-Name` 头传递账号

---

## 三、账户管理 API

### 3.1 注册账号
**接口**: `POST /api/account/register`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| password_confirm | string | 是 | 确认密码 |

**响应示例**:
```json
{
  "status": "success",
  "message": "注册成功"
}
```

---

### 3.2 账号登录
**接口**: `POST /api/account/login`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**响应示例**:
```json
{
  "status": "success",
  "message": "登录成功",
  "account_name": "用户名"
}
```

---

### 3.3 获取当前账号
**接口**: `GET /api/account/current`

**响应示例**:
```json
{
  "status": "success",
  "account_name": "用户名"
}
```

---

### 3.4 退出登录
**接口**: `POST /api/account/logout`

**响应示例**:
```json
{
  "status": "success",
  "message": "已退出账号"
}
```

---

## 四、角色管理 API

### 4.1 获取角色列表
**接口**: `GET /characters`

**响应示例**:
```json
{
  "characters": ["bigfoot", "english_tutor", "pirate", ...]
}
```

---

### 4.2 设置当前角色
**接口**: `POST /set_character`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| character | string | 是 | 角色名称 |

**响应示例**:
```json
{
  "status": "success",
  "message": "Character set to: english_tutor"
}
```

---

### 4.3 获取角色提示词
**接口**: `GET /api/character/{character_name}`

**路径参数**:
| 参数名 | 说明 |
|--------|------|
| character_name | 角色名称 |

**响应示例**:
```json
{
  "prompt": "You are a friendly English tutor..."
}
```

---

## 五、对话管理 API

### 5.1 启动对话
**接口**: `POST /start_conversation`

**响应示例**:
```json
{
  "status": "started"
}
```

---

### 5.2 停止对话
**接口**: `POST /stop_conversation`

**响应示例**:
```json
{
  "status": "stopped"
}
```

---

### 5.3 清除对话历史
**接口**: `POST /clear_history`

**请求头**:
| 参数名 | 说明 |
|--------|------|
| X-Account-Name | 账号名称(可选) |

**响应示例**:
```json
{
  "status": "cleared"
}
```

---

### 5.4 下载对话历史
**接口**: `GET /download_history`

**请求头**:
| 参数名 | 说明 |
|--------|------|
| X-Account-Name | 账号名称(可选) |

**响应**: 返回文本文件下载

---

## 六、语音处理 API

### 6.1 上传语音并处理
**接口**: `POST /api/voice/upload`

**请求表单**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| audio | file | 是 | 语音文件(webm格式) |
| character | string | 否 | 角色名称 |
| account_name | string | 否 | 账号名称 |

**响应示例**:
```json
{
  "status": "success",
  "transcription": "Hello, how are you?"
}
```

---

### 6.2 发送文字消息
**接口**: `POST /api/text/send`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| text | string | 是 | 消息内容 |
| character | string | 否 | 角色名称 |
| account_name | string | 否 | 账号名称 |

**响应示例**:
```json
{
  "status": "success",
  "message": "消息已发送"
}
```

---

### 6.3 练习模式转录
**接口**: `POST /api/practice/transcribe`

**请求表单**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| audio | file | 是 | 语音文件 |

**响应示例**:
```json
{
  "status": "success",
  "transcription": "Hello, how are you?",
  "audio_url": "/audio/practice/user_xxx.wav"
}
```

---

## 七、场景学习 API

### 7.1 获取大场景列表
**接口**: `GET /api/scene-npc/big-scenes`

**响应示例**:
```json
{
  "big_scenes": [
    {
      "id": "daily",
      "name": "日常生活",
      "image": "/images/big_daily.png"
    }
  ]
}
```

---

### 7.2 获取小场景列表
**接口**: `GET /api/scene-npc/small-scenes`

**查询参数**:
| 参数名 | 必填 | 说明 |
|--------|------|------|
| big_scene_id | 是 | 大场景ID |

**响应示例**:
```json
{
  "small_scenes": [
    {
      "id": "cafe",
      "name": "咖啡馆",
      "npcs": [...]
    }
  ]
}
```

---

### 7.3 获取NPC列表
**接口**: `GET /api/scene-npc/npcs`

**查询参数**:
| 参数名 | 必填 | 说明 |
|--------|------|------|
| small_scene_id | 是 | 小场景ID |
| account_name | 否 | 账号名称 |

**响应示例**:
```json
{
  "npcs": [
    {
      "id": "waiter",
      "name": "服务员",
      "learned": false,
      "has_content": true
    }
  ]
}
```

---

### 7.4 获取学习对话
**接口**: `GET /api/scene-npc/dialogue/learn`

**查询参数**:
| 参数名 | 必填 | 说明 |
|--------|------|------|
| small_scene_id | 是 | 小场景ID |
| npc_id | 是 | NPC ID |

**响应示例**:
```json
{
  "dialogue": {
    "small_scene_id": "cafe",
    "npc_id": "waiter",
    "content": [
      {"role": "A", "content": "Good morning!", "hint": "早上好"},
      {"role": "B", "content": "Good morning!", "hint": "早上好"}
    ]
  }
}
```

---

### 7.5 获取复习对话
**接口**: `GET /api/scene-npc/dialogue/review`

**查询参数**:
| 参数名 | 必填 | 说明 |
|--------|------|------|
| small_scene_id | 是 | 小场景ID |
| npc_id | 是 | NPC ID |

---

### 7.6 获取沉浸式对话
**接口**: `GET /api/scene-npc/dialogue/immersive`

**查询参数**:
| 参数名 | 必填 | 说明 |
|--------|------|------|
| small_scene_id | 是 | 小场景ID |
| npc_id | 是 | NPC ID |
| account_name | 否 | 账号名称 |

**响应示例**:
```json
{
  "dialogue": {
    "small_scene_id": "cafe",
    "npc_name": "服务员",
    "content": [...],
    "user_goal": "学习如何点咖啡"
  }
}
```

---

### 7.7 标记为已学习
**接口**: `POST /api/scene-npc/mark-learned`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| small_scene_id | string | 是 | 小场景ID |
| npc_id | string | 是 | NPC ID |

**响应示例**:
```json
{
  "status": "success",
  "newly_unlocked": ["hospital"]
}
```

---

### 7.8 沉浸式自由对话
**接口**: `POST /api/scene-npc/immersive-chat`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| small_scene_id | string | 是 | 小场景ID |
| npc_id | string | 是 | NPC ID |
| message | string | 是 | 用户消息 |
| history | array | 否 | 对话历史 |
| role_swapped | boolean | 否 | 是否交换角色 |

**响应示例**:
```json
{
  "status": "success",
  "reply": "What would you like to order?",
  "task_completed": false,
  "audio_url": "/audio/immersive/reply_xxx.wav"
}
```

---

### 7.9 生成沉浸式对话报告
**接口**: `POST /api/scene-npc/immersive-chat/report`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| small_scene_id | string | 是 | 小场景ID |
| npc_id | string | 是 | NPC ID |
| transcript | array | 是 | 对话记录 |

**响应示例**:
```json
{
  "status": "success",
  "report_markdown": "## 纠错与改进
...",
  "reference_script": "A: Good morning!
B: Good morning!",
  "core_sentences": "Good morning!",
  "core_chunks": "good morning"
}
```

---

## 八、练习模式 API

### 8.1 开始练习
**接口**: `POST /api/practice/start`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dialogue | string | 是 | 对话内容 |
| dialogue_lines | array | 否 | 对话行(含音频URL) |
| dialogue_id | string | 否 | 对话ID |
| small_scene_id | string | 否 | 小场景ID |
| npc_id | string | 否 | NPC ID |
| account_name | string | 否 | 账号名称 |

**响应示例**:
```json
{
  "status": "success",
  "session_id": "uuid-xxx",
  "dialogue_id": "cafe-waiter-learn",
  "dialogue_lines": [...],
  "current_turn": 0,
  "a_text": "Good morning!",
  "a_audio_url": "/audio/xxx.wav",
  "b_hints": {
    "phrases": ["Good morning!"],
    "key_sentence": "Good morning!"
  },
  "total_turns": 3
}
```

---

### 8.2 用户回复验证
**接口**: `POST /api/practice/respond`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_input | string | 是 | 用户输入 |
| dialogue_lines | array | 是 | 对话行 |
| current_turn | number | 是 | 当前轮次 |
| session_id | string | 是 | 会话ID |

**响应示例**:
```json
{
  "status": "success",
  "is_consistent": true,
  "validation_result": {
    "result": "consistent",
    "reason": "意思一致"
  },
  "next_a_text": "What can I get you?",
  "next_a_audio_url": "/audio/xxx.wav",
  "next_b_hints": {...},
  "next_turn": 1,
  "is_completed": false
}
```

---

### 8.3 结束练习
**接口**: `POST /api/practice/end`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 会话ID |

**响应示例**:
```json
{
  "status": "success",
  "session_data": {
    "dialogue_id": "...",
    "user_inputs": [...],
    "dialogue_topic": "日常对话"
  }
}
```

---

### 8.4 生成复习笔记
**接口**: `POST /api/practice/generate-review`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_inputs | array | 是 | 用户输入列表 |
| dialogue_topic | string | 是 | 对话主题 |
| dialogue_id | string | 否 | 对话ID |
| small_scene_id | string | 否 | 小场景ID |
| npc_id | string | 否 | NPC ID |

**响应示例**:
```json
{
  "status": "success",
  "review_notes": {
    "corrections": [
      {
        "user_said": "I want coffee",
        "correct": "I'd like a coffee",
        "explanation": "用 would like 更礼貌"
      }
    ],
    "core_sentences": "I'd like...",
    "core_chunks": "would like",
    "review_dialogue": [...]
  }
}
```

---

## 九、学习进度 API

### 9.1 获取学习推荐
**接口**: `POST /api/learning/recommend`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_name | string | 否 | 账号名称 |
| conversation_summary | string | 否 | 对话摘要 |
| count | number | 否 | 推荐数量(默认4) |

**响应示例**:
```json
{
  "recommendations": [
    {
      "small_scene_id": "cafe",
      "npc_id": "waiter",
      "npc_name": "服务员"
    }
  ]
}
```

---

### 9.2 开始英文学习阶段
**接口**: `POST /api/learning/start_english`

**请求头**:
| 参数名 | 说明 |
|--------|------|
| X-Account-Name | 账号名称 |

**响应示例**:
```json
{
  "status": "success",
  "message": "已切换到英文学习阶段"
}
```

---

### 9.3 更新英文水平
**接口**: `POST /api/user/update_english_level`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| level | string | 是 | 级别(beginner/intermediate/advanced) |
| description | string | 否 | 描述 |
| account_name | string | 否 | 账号名称 |

---

### 9.4 标记单元已掌握
**接口**: `POST /api/practice/mark-unit-mastered`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dialogue_id | string | 否 | 对话ID |
| small_scene_id | string | 否 | 小场景ID |
| npc_id | string | 否 | NPC ID |
| account_name | string | 否 | 账号名称 |

---

### 9.5 保存练习记忆
**接口**: `POST /api/practice/save-memory`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| small_scene_id | string | 是 | 小场景ID |
| npc_id | string | 是 | NPC ID |
| account_name | string | 否 | 账号名称 |

---

## 十、英文卡片 API

### 10.1 生成英文对话卡片
**接口**: `POST /api/english/generate`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| small_scene_id | string | 是 | 小场景ID |
| npc_id | string | 是 | NPC ID |
| account_name | string | 否 | 账号名称 |

**响应示例**:
```json
{
  "status": "success",
  "dialogue": "A: Good morning!
B: Good morning!",
  "dialogue_lines": [
    {"speaker": "A", "text": "Good morning!", "audio_url": "/audio/xxx.wav"},
    {"speaker": "B", "text": "Good morning!", "audio_url": null}
  ],
  "dialogue_id": "cafe-waiter-learn",
  "card_title": "咖啡馆 - 点单"
}
```

---

### 10.2 结束对话并生成卡片
**接口**: `POST /api/conversation/end`

**请求头**:
| 参数名 | 说明 |
|--------|------|
| X-Account-Name | 账号名称 |

**响应示例**:
```json
{
  "status": "success",
  "message": "对话已结束，记忆已保存",
  "should_generate_english": true,
  "big_scenes": [...]
}
```

---

## 十一、知识库 API

### 11.1 获取可选场景
**接口**: `GET /api/knowledge/available-scenes`

**请求头**:
| 参数名 | 说明 |
|--------|------|
| X-Account-Name | 账号名称 |

**响应示例**:
```json
{
  "status": "success",
  "suggested_scene": "cafe",
  "available_scenes": ["cafe", "restaurant", "hospital"],
  "available_difficulties": ["easy", "medium", "hard"]
}
```

---

### 11.2 选择场景
**接口**: `POST /api/knowledge/select-scene`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| scene | string | 是 | 场景ID |
| difficulty | string | 否 | 难度级别 |
| account_name | string | 否 | 账号名称 |

---

### 11.3 获取推荐知识点
**接口**: `GET /api/knowledge/recommended`

**查询参数**:
| 参数名 | 说明 |
|--------|------|
| account_name | 账号名称 |
| label_id | 标签ID |
| scene_primary | 主要场景 |
| scene_secondary | 次要场景 |

---

## 十二、1v1 真人练习 API

### 12.1 获取已解锁场景
**接口**: `GET /api/practice-live/unlocked-scenes`

**查询参数**:
| 参数名 | 说明 |
|--------|------|
| account_name | 账号名称 |

**响应示例**:
```json
{
  "small_scene_ids": ["cafe", "restaurant"]
}
```

---

### 12.2 获取对话
**接口**: `GET /api/practice-live/dialogue`

**查询参数**:
| 参数名 | 说明 |
|--------|------|
| small_scene_id | 小场景ID |
| room_id | 房间ID(保证同房间同一主题) |

---

### 12.3 随机获取对话
**接口**: `GET /api/practice-live/dialogue/random`

**查询参数**:
| 参数名 | 说明 |
|--------|------|
| room_id | 房间ID |

---

### 12.4 获取后端配置
**接口**: `GET /api/practice-live/config`

**响应示例**:
```json
{
  "backendUrl": "https://varta.example.com"
}
```

---

### 12.5 获取在线用户数
**接口**: `GET /api/practice-live/user-count`

**响应示例**:
```json
{
  "userCount": 42
}
```

---

## 十三、WebSocket API

### 13.1 标准对话 WebSocket
**接口**: `WS /ws`

**客户端发送**:
```json
// 设置账号
{"action": "set_account", "account_name": "用户名"}

// 启动对话
{"action": "start", "character": "english_tutor"}

// 停止对话
{"action": "stop"}

// 设置角色
{"action": "set_character", "character": "pirate"}

// 设置API供应商
{"action": "set_api_provider", "provider": "openai"}

// 设置语音
{"action": "set_openai_voice", "voice": "alloy"}

// 清除历史
{"action": "clear"}
```

**服务端推送**:
```json
// 用户消息
{"action": "user_message", "text": "Hello"}

// AI音频
{"action": "ai_audio", "audio_url": "/audio/tts/xxx.wav"}

// 录音状态
{"action": "recording_started"}
{"action": "recording_stopped"}

// 错误
{"action": "error", "message": "Error occurred"}
```

---

### 13.2 增强模式 WebSocket
**接口**: `WS /ws_enhanced`

用于实时语音对话，保持长连接。

---

## 十四、配置类 API

### 14.1 获取增强模式默认配置
**接口**: `GET /enhanced_defaults`

**响应示例**:
```json
{
  "character": "english_tutor",
  "voice": "alloy",
  "model": "gpt-4o-mini",
  "tts_model": "gpt-4o-mini-tts",
  "transcription_model": "gpt-4o-mini-transcribe"
}
```

---

### 14.2 获取 Ollama 模型列表
**接口**: `GET /ollama_models`

**响应示例**:
```json
{
  "models": ["llama3.2", "llama3.1", "qwen2.5"]
}
```

---

### 14.3 设置转录模型
**接口**: `POST /set_transcription_model`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model | string | 是 | 模型名称 |

---

### 14.4 获取 Kokoro 语音列表
**接口**: `GET /kokoro_voices`

**响应示例**:
```json
{
  "voices": [
    {"id": "af_bella", "name": "Bella (Female) - American English"},
    {"id": "bm_daniel", "name": "Daniel (Male) - American English"}
  ]
}
```

---

### 14.5 获取 ElevenLabs 语音列表
**接口**: `GET /elevenlabs_voices`

---

### 14.6 获取 OpenAI 临时密钥
**接口**: `GET /openai_ephemeral_key`

**响应示例**:
```json
{
  "client_secret": {
    "value": "sk-xxx"
  }
}
```

---

### 14.7 OpenAI Realtime 代理
**接口**: `POST /openai_realtime_proxy`

用于 WebRTC 连接代理，解决 CORS 问题。

---

## 十五、页面路由

| 路由 | 说明 |
|------|------|
| `/` | 默认英语学习页面 |
| `/voice_chat` | 语音聊天页面 |
| `/enhanced` | 增强模式页面 |
| `/webrtc_realtime` | WebRTC 实时语音页面 |
| `/practice/live` | 1v1 真人练习页面 |
| `/scene/{scene_id}` | 场景页面 |
| `/scenes` | 场景列表页 |

---

## 十六、错误码说明

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未登录/认证失败 |
| 403 | 权限不足/未解锁 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 附录: 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| API_PROVIDER | API供应商(openai/doubao) | doubao |
| OPENAI_API_KEY | OpenAI API密钥 | - |
| DOUBAO_API_KEY | 豆包API密钥 | - |
| MODEL_PROVIDER | 模型供应商 | openai |
| TTS_PROVIDER | TTS供应商 | openai |
| CHARACTER_NAME | 默认角色 | english_tutor |
| OPENAI_TTS_VOICE | OpenAI TTS音色 | alloy |
| VOICE_SPEED | 语音速度 | 1.0 |
| MAX_CHAR_LENGTH | 最大字符数 | 500 |

---

*文档生成时间: 2026-03-01*
*English-Chat-AI 项目接口手册 v1.0*
