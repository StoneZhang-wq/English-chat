# backend（MyEnglishChat 新后端 · 规划中）

与 **`MyEnglishChatApplication/`** 并列。本目录为 **正式后端** 工程位置（**Python**，建议 **FastAPI**）。

详细**框架、分层、通常包含哪些模块**见工作区文档：**`docs/TECH-ARCHITECTURE.md` §5**。

## 与 English-Chat 的关系

- **`English-Chat/`** 为历史网页版及旧服务端，**不再作为产品使用**。
- 在此实现新 API 时，可对照 English-Chat 的 `routers/`、`service/`、`crud/` 等**重写**，**不要**把旧项目当运行依赖。

## 职责（规划摘要）

- HTTP/WebSocket API、鉴权与用户
- **LLM**（如豆包）代理，密钥仅在后端
- 场景、练习、会话等业务（按产品裁剪）
- **P2P**：声网 Agora 或 腾讯云 TRTC 的 Token / 房间等（选型落定后补充）

实现启动后请在本目录补充 `requirements.txt`、运行方式与环境变量说明。
