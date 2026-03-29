# English-Chat 项目架构说明

本文档描述当前项目的文件组织结构、模块职责与数据库表用途，供开发者遵循以保持架构一致、避免破坏现有约定。

---

## 一、技术栈与入口

- **后端**：FastAPI，异步（async/await）
- **数据库**：MySQL，ORM 为 SQLAlchemy（async，aiomysql）
- **缓存**：Redis（AsyncRedisCache）
- **前端**：Jinja2 模板 + 静态资源（HTML/CSS/JS），无 SPA 框架
- **认证**：Bearer Token，前端使用 **sessionStorage** 存 `token`、`current_account`、`current_user_id`（不使用 localStorage，以便关页即失效）
- **入口**：`main.py`，启动时执行 lifespan（清 Redis、建表、从 JSON 初始化场景数据）

---

## 二、文件组织结构

```
English-Chat/
├── main.py                 # FastAPI 应用入口，路由挂载、静态/模板路径、lifespan
├── config.py               # 配置类 Config，从 .env 读取（数据库、Redis、LLM、TTS 等）
├── run.py                  # 可选运行入口
│
├── routers/                # HTTP 路由层，仅处理请求/响应与依赖注入，业务逻辑放在 service/crud
│   ├── api.py              # /api：练习模式、学习推荐、对话生成、练习 start/respond/end、复习生成、保存进度等
│   ├── auth.py             # /api/account：注册、登录、登出、当前用户
│   ├── admin.py            # /api/admin：用户管理（列表、分页、统计、增删改），仅 username=admin 可访问
│   ├── ai_chat.py          # /api/chat：自然对话 /practice、/summary（学习卡片摘要）
│   ├── scene.py            # /api/scene-npc：大/小场景、NPC、dialogue/learn、dialogue/immersive、immersive-chat、immersive-chat/report
│   ├── audio.py            # /api/audio：TTS 文件服务 /tts/{path}、/english_dialogue/{dialogue_id}/{path}，临时 /temp/{token}
│   └── websocket.py        # WebSocket 连接管理
│
├── service/                # 业务与外部服务
│   ├── agent.py            # ChatAgent：LLM 调用封装（generate_chat）、TTS 流程、ASR 转写、会话流程 generate_chat_flow
│   ├── database.py         # 异步引擎 async_engine、AsyncSessionLocal、get_db 依赖
│   ├── redis_cache.py      # 异步 Redis 缓存封装
│   ├── conn_manager.py     # WebSocket 连接管理（按 user_id/channel）
│   ├── scene_manager.py    # 场景/对话数据统一入口：get_dialogues、get_big_scenes、get_small_scenes 等，优先缓存，其他逻辑基于三者过滤
│   ├── init_scene_data.py  # 启动时从 resource 下 JSON 增量同步到 BigScene、SmallScene、Dialogue（主键存在则忽略）
│   ├── practice.py         # 练习模式逻辑：首轮/下一轮、hints、完成判定等
│   ├── prompt.py           # 各类 LLM 提示词：沉浸式对话、报告、练习校验、复习纠错、用户档案等
│   ├── doubao.py           # 豆包 TTS/ASR：generate_speech、generate_tts_for_dialogue_lines（english_dialogue 目录），并发限制 Semaphore
│   ├── openai.py           # OpenAI 兼容 API 的 LLM 调用
│   ├── gemini.py           # Gemini LLM 调用
│   └── protocols/          # 豆包 TTS 等协议相关
│
├── crud/                   # 数据库增删改查，不包含业务规则
│   ├── users.py            # 用户 CRUD、分页列表、在线状态、注册/更新请求体
│   ├── chat.py             # ChatSession、ChatMessage 的创建、列表、添加消息
│   ├── dialogue.py         # Dialogue 表查询（如按 dialogue_id）
│   ├── scene.py            # BigScene、SmallScene 查询（如按 id/immersive）
│   ├── scene_study.py      # NpcLearnProgress：学习进度 process（JSON 数组 dialogue_id）、追加 dialogue_id
│   └── diary.py            # 日记 CRUD
│
├── models/                 # SQLAlchemy ORM 模型，与表一一对应
│   ├── base.py             # Base、SceneType 枚举、generate_uuid
│   ├── users.py            # User
│   ├── chat.py             # ChatSession、ChatMessage
│   ├── scene.py            # BigScene、SmallScene
│   ├── dialogue.py         # Dialogue
│   ├── scene_npc.py        # NpcLearnProgress
│   └── diary.py            # Diary
│
├── utils/                  # 通用工具与中间件
│   ├── auth.py             # get_current_user、get_current_admin（admin 仅按 username=="admin" 判断）
│   ├── response.py        # 统一响应格式 success_response 等
│   ├── logger_manager.py   # 日志
│   ├── exception_handlers.py # 全局异常处理注册
│   ├── security.py         # 密码哈希等
│   └── tools.py            # 通用小工具
│
├── frontend/
│   ├── templates/          # Jinja2 页面
│   │   ├── voice_chat.html      # 主界面：登录/注册、角色选择、练习模式、学习卡片、沉浸式入口
│   │   ├── user_management.html # 用户管理（管理员）
│   │   ├── scene.html           # 场景相关
│   │   └── ...
│   └── static/
│       ├── css/            # 样式
│       └── js/             # 前端逻辑
│           ├── core.js         # API 封装、token 从 sessionStorage 读取
│           ├── voice_chat.js   # 主界面：账号、练习、学习卡片、沉浸式流程
│           ├── scene_modal.js  # 场景选择、沉浸式对话 UI、报告
│           ├── user_management.js
│           └── ...
│
├── resource/               # 静态配置数据，启动时同步到 DB
│   ├── scenes/             # scene_npc_index.json、scenes.json 等
│   └── dialogues/          # dialogues.json
│
├── data/                   # 运行时生成，不提交版本库（见 .gitignore）
│   ├── audio/tts/          # 用户级 TTS：自然对话、沉浸式 AI 回复，按 user_id 分子目录
│   └── english_dialogue/  # 固定剧本 TTS：按 dialogue_id 分目录，多用户复用，练习/复习音频
│
├── characters/             # 角色配置（名称、提示等）
└── doc/                    # 文档
    ├── PROJECT_ARCHITECTURE.md  # 本架构说明
    └── English-Chat-AI-接口手册.md
```

---

## 三、模块说明与约定

### 3.1 路由层（routers）

- **职责**：解析请求、校验参数、调用 service/crud、返回统一响应；不直接写复杂业务逻辑。
- **依赖**：通过 `Depends(get_current_user)` / `Depends(get_current_admin)` 做鉴权，通过 `Depends(get_db)` 注入会话，通过 `Depends(get_agent_service)` 注入 ChatAgent。
- **约定**：
  - 场景/对话数据**必须**通过 `service.scene_manager` 的 `get_dialogues`、`get_big_scenes`、`get_small_scenes` 等统一接口获取，**禁止**在 router 或任意业务层直接对 Dialogue/BigScene/SmallScene 表做 crud 查询（除 init_scene_data 的增量写入外）。

### 3.2 服务层（service）

- **scene_manager**：场景与对话数据的**唯一数据入口**。所有需要“对话列表、大/小场景、按场景过滤”的逻辑均基于 `get_dialogues`、`get_big_scenes`、`get_small_scenes` 的返回做过滤或聚合，不直接调用 crud 查 Dialogue/BigScene/SmallScene。
- **agent**：统一 LLM 调用（generate_chat）、TTS 流程、ASR、会话流程；LLM 提供商由 config 决定（OpenAI / Gemini 等）。
- **doubao**：TTS 写入路径约定——自然对话/沉浸式单条回复写入 `./data/audio/tts/{user_id}/`；固定剧本（练习/复习）写入 `./data/english_dialogue/{dialogue_id}/`，文件名与练习模式一致（如 A_0.wav），可复用。
- **init_scene_data**：仅负责从 `resource/` 下 JSON 按主键增量同步到 DB（主键已存在则跳过），不删除已有数据。

### 3.3 数据层（crud / models）

- **crud**：仅做数据库增删改查与简单 DTO 转换，不包含“推荐逻辑、是否解锁”等业务规则；业务规则放在 service（如 scene_manager、practice）。
- **models**：表结构以当前代码为准；新增表或字段时需在 `models/__init__.py` 导出，并在 `main.py` lifespan 前 import 以便 `Base.metadata.create_all` 建表。

### 3.4 前端约定

- **认证**：token、current_account、current_user_id 仅使用 **sessionStorage**，关页即失效；登出或 pagehide 时调用登出接口并清空 sessionStorage。
- **API 基址**：通过 `core.js` 等统一封装，请求头携带 `Authorization: Bearer <token>`，token 从 sessionStorage 读取。

---

## 四、数据库表用途

| 表名 | 用途 | 说明 |
|------|------|------|
| **users** | 用户账号与档案 | 用户名、邮箱、密码、姓名、英语水平、年龄、职业、目标、习惯、兴趣、偏好、是否在线等。管理员仅通过 username 是否为 "admin" 判断。 |
| **chat_sessions** | 聊天会话 | 每条会话归属一个 user_id，带 scene_type（自然对话/场景练习/AI 对话等）、title、创建/更新时间。 |
| **chat_messages** | 会话消息 | 归属 session_id，含 role（user/assistant）、character、content。自然对话与沉浸式对话内容存于此。 |
| **big_scene** | 大场景 | 如 daily、food、transport；id、name、sort_order。与 resource 中 big_scenes 对应。 |
| **small_scene** | 小场景 | 归属 big_scene_id，如 home、cafe；含 immersive_scene_id（可与 id 不同，如 hospital→clinic）。 |
| **dialogue** | 对话配置 | 一段剧本一条记录：dialogue_id（业务唯一）、big_scene_id、small_scene_id、npc、usage（learn/review/immersive）、content（JSON 数组）、core_sentences、core_chunks、npc_name、user_goal、user_goal_a 等。learn 用于练习与推荐，review 用于复习，immersive 用于自由对话剧本与报告参考。 |
| **npc_learn_progress** | NPC 学习进度 | 每用户一条，process 为 JSON 数组，存已学 dialogue_id 列表，用于“是否解锁某小场景/某 NPC”及推荐。 |
| **diary** | 学习日记 | 用户日记条，可选关联 scene_type、session_id。 |

---

## 五、关键 API 前缀与职责速览

| 前缀 | 职责 |
|------|------|
| /api/account | 注册、登录、登出、当前用户 |
| /api/admin | 用户管理（需 admin） |
| /api/chat | 自然对话 /practice、学习摘要 /summary |
| /api | 练习模式：/learning/recommend、/english/generate、/practice/start、/practice/respond、/practice/end、/practice/generate-review、/practice/save-memory 等 |
| /api/scene-npc | 大/小场景、NPC 列表、dialogue/learn、dialogue/immersive、immersive-chat、immersive-chat/report |
| /api/audio | TTS 文件服务：/tts、/english_dialogue/{dialogue_id} |

---

## 六、开发者约束（系统提示词）

在修改或扩展本系统时，请遵守以下约束：

1. **场景与对话数据**：仅通过 `service.scene_manager` 的 `get_dialogues`、`get_big_scenes`、`get_small_scenes`（及其衍生接口）获取场景与对话数据；不得在 routers 或其它 service 中直接对 Dialogue、BigScene、SmallScene 表执行 crud 查询。
2. **认证与前端状态**：前端仅使用 sessionStorage 存储 token 与当前用户信息；管理员判断仅依据 `username == "admin"`。
3. **TTS 存储**：用户自然对话与沉浸式单条回复的 TTS 存于 `./data/audio/tts/{user_id}/`；固定剧本（练习/复习）的 TTS 存于 `./data/english_dialogue/{dialogue_id}/`，命名与现有练习模式一致以便复用。
4. **会话与历史**：沉浸式对话在 GET dialogue/immersive 时创建 ChatSession 并返回 session_id；immersive-chat 将历史从该 session 的 chat_messages 中读取并作为 LLM 上下文，不得仅依赖前端上传的 history 作为唯一上下文。
5. **数据初始化**：场景与对话的初始数据来自 `resource/` 下 JSON；init_scene_data 仅做按主键增量插入，不删除已有记录。
6. **新增表或模型**：在 `models/` 中定义并在 `models/__init__.py` 与 `main.py` 的模型 import 中登记，以保证 lifespan 建表正确。

以上约定用于保持架构一致、数据源统一、认证与存储行为可预期，请勿绕过或违反。
