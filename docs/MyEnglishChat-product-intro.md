# MyEnglishChat 产品介绍

## 产品名称与品牌

**MyEnglishChat** 为当前主产品（Flutter 应用：Android+iOS）。历史项目 **English-Chat（EchoEnglish 网页版）** **不再作为产品使用**，仅保留在仓库中作为**业务与接口设计的参考**，用于对照重写**移动端**与**新后端**。

---

## 一句话介绍

**MyEnglishChat 是一款面向真实情境的英语口语训练移动应用（Flutter：Android+iOS）：以 Learn（AI 学习与陪练）完成从“输入（听）”到“输出（说）”的闭环训练，再通过 P2P Match（真人 1v1 语境实战）在真实压力下检验效果，并在 Profile 沉淀数据与设置；ASR/TTS 以端侧为主，LLM 统一经自有 FastAPI 后端转发。**

---

## 产品定位

- **用户**：需要在面试、会议、旅行、就医等场景中实际使用英语的学习者。
- **价值**：在情境中开口练习；AI 反馈与重复练习；真人板块上线后可与他人角色扮演练习。
- **形态**：**客户端**为 Flutter 应用（Android+iOS，目录 `app_flutter/`）；**服务端**为与客户端**并列目录** **`backend/`**（Python + FastAPI）；**English-Chat 不参与正式上线链路**。

---

## 功能板块（用户视角）

### 1）Learn（核心学习与 AI 陪练）

- **场景探索（Scenario Discovery）**：支持层级筛选  
  - 大场景（如职场）→ 小场景（如面试）→ NPC（如 HR Heather）→ 具体话题（如行为面试题）  
  - 支持全局搜索关键词（如 “Coffee / Order / Interview”）快速直达剧本
- **学习模式三部曲（Learning Modes）**：选定话题后进入学习界面，通过顶部 Tab 切换三种递进模式  
  - **Mode A：Shadowing（沉浸式跟读，练发音）**：播放原音（原速/慢速）+ 按住录音模仿；提供波形反馈与简单发音相似度提示  
  - **Mode B：Practice（剧本角色扮演，练流利度）**：按既定剧本分角色朗读；轮到用户时提供提词器；用户语音输入后 AI 自动接下一句  
  - **Mode C：AI Dialogue（开放式自由对话，练应变）**：给定任务目标（Task）+ NPC 人设；用户自由语音输入；支持 “Hint（提示）”给一句推荐表达
- **学习反馈（Performance Review）**：在 Practice 或 AI Dialogue 结束后生成复盘报告，指出语法/发音问题并提供更地道表达建议

### 2）P2P Match（真人 1v1 语境实战）——开发中

- **剧本大厅（Scenario Lobby）**：选择刚在 Learn 练过的场景，或从 Trending 挑选一个场景作为通话剧本  
- **智能匹配（Smart Match）**：匹配同/相似场景的用户；雷达搜索动画；成功后进入实战房间  
- **实战房间（Roleplay Room）**：音视频/纯语音通话；明确角色分配与任务目标（Task）；提供破冰提示词与场景词汇；支持 Role Swap 再练一轮  

实时音视频能力暂定接入 **声网 Agora** 或 **腾讯云 TRTC**；Token 由 **新后端**签发，客户端仅集成官方 SDK。

### 3）Profile / Settings（个人中心与数据沉淀）

登录、学习记录与偏好设置等；由 **新后端** 提供接口（可参考 English-Chat 账号设计，不强制兼容旧库）。

---

## 技术说明（简版）

- **客户端**：Flutter + Material 3；底部三主板块：**Learn / P2P Match / Profile**。
- **语音**：ASR / TTS 以**端侧**为主（规划与迭代中）。
- **大模型**：云端 LLM，经 **`backend/`（Python FastAPI）** 代理；**English-Chat 不作为正式 API 宿主**。
- **真人**：**声网 / 腾讯云 TRTC** 二选一待定；服务端配置与 Token，客户端集成官方 SDK。
- **参考**：**English-Chat** 仓库用于查阅旧有路由、业务与数据模型，**不**继续维护网页产品。

---

## 网页版（参考）↔ 移动端（主产品）

| 原 English-Chat（仅参考） | MyEnglishChat（实现目标） |
|---------------------------|---------------------------|
| 场景、练习、语音相关逻辑 | **Learn**（Shadowing / Practice / AI Dialogue） |
| AI 对话、实时链路思路 | **Learn → AI Dialogue** |
| 真人 1v1 思路 | **P2P Match**（RTC + 新后端） |
| 账号体系思路 | **Profile / Settings**（新后端） |

---

*随产品迭代更新。*

技术架构见 **[TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md)**（Flutter 目录、API 与迭代见 §4）。
