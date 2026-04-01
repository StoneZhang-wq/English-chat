# RESTful API Inventory (from English-Chat)

This file summarizes legacy API routes from `English-Chat` and current migration status in `backend`.

## Scope

- Source of truth for legacy routes:
  - `English-Chat/routers/auth.py`
  - `English-Chat/routers/api.py`
  - `English-Chat/routers/scene.py`
  - `English-Chat/routers/practice_live.py`
  - `English-Chat/routers/ai_chat.py`
  - `English-Chat/routers/admin.py`
- Current app-side usage source:
  - `app_flutter/lib/data/repositories/practice_chat_repository.dart`

## Legacy API groups

- `account`
  - `POST /api/account/register`
  - `POST /api/account/login`
  - `POST /api/account/logout`
  - `GET /api/account/current`

- `characters and voice`
  - `GET /api/characters`
  - `POST /api/voice/upload`
  - `POST /api/practice/transcribe`

- `learning and practice`
  - `POST /api/learning/recommend`
  - `POST /api/english/generate`
  - `POST /api/practice/start`
  - `POST /api/practice/respond`
  - `POST /api/practice/end`
  - `POST /api/practice/generate-review`
  - `POST /api/practice/save-memory`
  - `POST /api/practice/mark-unit-mastered`

- `scene and immersive chat`
  - `GET /api/scene-npc/big-scenes`
  - `GET /api/scene-npc/small-scenes`
  - `GET /api/scene-npc/immersive-small-scenes`
  - `GET /api/scene-npc/npcs`
  - `GET /api/scene-npc/dialogue/learn`
  - `GET /api/scene-npc/dialogue/review`
  - `GET /api/scene-npc/dialogue/immersive`
  - `POST /api/scene-npc/immersive-chat`
  - `POST /api/scene-npc/immersive-chat/report`

- `practice live`
  - `GET /api/practice-live/unlocked-scenes`
  - `GET /api/practice-live/dialogue`
  - `GET /api/practice-live/dialogue/random`
  - `GET /api/practice-live/config`
  - `GET /api/practice-live/user-count`

- `admin`
  - `GET /api/admin/users/stats`
  - `GET /api/admin/users`
  - `PUT /api/admin/users/{user_id}`
  - `DELETE /api/admin/users/{user_id}`

## Backend migration status (current)

- Implemented in `backend`:
  - `POST /api/practice/chat`
  - `GET /health`

- Needed by current `app_flutter` code:
  - `POST /api/practice/chat` (already wired)

- Not yet implemented in `backend`:
  - All remaining legacy routes listed above

## Current `POST /api/practice/chat` contract

- Request JSON
  - `messages: [{ role: "user" | "assistant", content: string }]`
  - `scenario_title?: string`
- Response JSON
  - `{ "reply": "..." }`
- Notes
  - Server injects `system` prompt
  - Unknown roles and empty content are ignored
  - History is truncated to a safe size before calling LLM
