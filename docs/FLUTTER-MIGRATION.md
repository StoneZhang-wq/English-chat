# Kotlin/Compose → Flutter 迁移说明（MyEnglishChat）

## 1. 目标与范围

- **目标**：主客户端统一迁移到 `app_flutter/`（Flutter，Android+iOS）。
- **保留**：`backend/`（Python + FastAPI）作为唯一服务端。
- **降级**：`MyEnglishChatApplication/` 作为历史参考与迁移对照，不再作为主线继续堆功能。

## 2. 迁移原则

- **先跑通再重构**：先把核心链路（Practice 文本 + 语音）迁移可用，再逐步拆分 feature、完善状态管理与测试。
- **语音链路主线（端侧 Vosk）**：
  - 录音 → 本地转写（Vosk）→ 把转写文本送到 `backend` → 返回 LLM 回复
  - UX：松手立刻显示语音气泡「转写中…」，完成后更新同一条消息
  - 停录边界：先 stop-capture（轻量）再异步 finalize（IO），避免多录静音
- **Base URL 可配置**：debug/真机/模拟器需可切换（Flutter 用 `--dart-define=BACKEND_BASE_URL=...`）。
- **密钥只在后端**：客户端不得内置任何云厂商密钥或 Token 生成逻辑。

## 3. 迁移阶段建议

### 阶段 A：Flutter 外壳与路由
- 三 Tab（Shadowing / Practice / P2P）
- 主题与基础组件

### 阶段 B：Practice 文本链路
- 对话列表 UI
- 文本发送 → `backend` → 展示 AI 回复

### 阶段 C：Practice 语音链路（端侧）
- 录音（WAV/PCM）与语音气泡
- Vosk 模型预取与转写

### 阶段 D：Shadowing / P2P
- 场景列表、跟读播放
- RTC 选型落地后再接 SDK

