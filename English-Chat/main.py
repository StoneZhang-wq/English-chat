import os
import re
import shutil
import signal
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, JSONResponse, Response
from routers import auth, api, admin, websocket, ai_chat, audio, scene, practice_live
from config import configer
from service.database import async_engine, AsyncSessionLocal
from service.redis_cache import AsyncRedisCache
from models.base import Base
from service.init_scene_data import load_data_from_json
# 导入所有模型以便 Base.metadata.create_all 创建全部表
from models import (  # noqa: F401
    User, ChatMessage, ChatSession,
    BigScene, SmallScene, Dialogue, NpcLearnProgress, Diary,
)
from contextlib import asynccontextmanager
from utils.exception_handlers import register_exception_handlers
from utils import logger

VERSION = "1.0.0"


# async def audit_middleware_lite(request: Request, call_next):
#     # 审计逻辑
#     start_time = datetime.now()
#     response = await call_next(request)
#     process_time = (datetime.now() - start_time).total_seconds()
#
#     # 记录审计日志（示例）
#     logger.info(f"AUDIT: {request.method} {request.url.path} - {response.status_code} - {process_time}s")
#     return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：尽量完成 Redis 清理、建表、初始化；任一步失败也不阻塞应用启动，保证能响应请求
    cache = AsyncRedisCache(enable_stats=False)
    try:
        await cache.clear()
        logger.info("Redis cache cleared on startup")
    except Exception as e:
        logger.warning("Redis cache clear on startup failed: %s", e)
    finally:
        try:
            await cache.close()
        except Exception:
            pass

    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await load_data_from_json(session)
    except Exception as e:
        logger.warning("DB init or scene data load failed (app will still run): %s", e)

    yield
    # 关闭时：清理资源
    try:
        await async_engine.dispose()
    except Exception:
        pass


app = FastAPI(
    title="English Chat API",
    version="1.0.0",
    description="A English practice platform",
    lifespan=lifespan
)

# 注册异常处理器
register_exception_handlers(app)

#app.middleware("http")(audit_middleware_lite)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # 允许的源，开发阶段允许所有源，生产环境需要指定源
    allow_credentials=True,  # 允许携带cookie
    allow_methods=["*"],     # 允许的请求方法
    allow_headers=["*"],     # 允许的请求头
)

# 前端路径：以 main.py 所在目录为基准，兼容本地与 Railway 部署
_main_dir = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.join(_main_dir, "frontend")
static_path = os.path.join(frontend_path, "static")
template_path = os.path.join(frontend_path, "templates")

if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    app.mount("/frontend/static", StaticFiles(directory=static_path), name="frontend_static")

templates = Jinja2Templates(directory=template_path)

# 挂载路由/注册路由
app.include_router(api.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(websocket.router)
app.include_router(ai_chat.router)
app.include_router(audio.router)
app.include_router(scene.router)
app.include_router(practice_live.router)

# 真人 1v1 练习（同源 SPA）
_BASE_DIR = Path(__file__).resolve().parent
_PRACTICE_LIVE_DIR = _BASE_DIR / "static" / "practice-live"

# 画风与主站统一：注入的样式表与字体（theme 走专用路由，不缓存，改完即生效）
_PRACTICE_LIVE_THEME_CSS_URL = "/practice/live/theme.css"
# 覆盖样式文件：实际存放在 frontend/static/css 下，避免与主站 css 混淆
_PRACTICE_LIVE_OVERRIDE_CSS_PATH = _BASE_DIR / "frontend" / "static" / "css" / "practice-live-override.css"
_INTER_FONT_URL = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
_503_HTML = (
    "<!DOCTYPE html><html><body style='font-family:sans-serif;padding:2rem;'>"
    "<h1>真人练习未就绪</h1>"
    "<p>请先在项目根目录执行 <code>npm run build:practice-live</code>，"
    "并将构建输出复制到 <code>app/static/practice-live/</code>。</p></body></html>"
)

def _practice_live_index_response() -> HTMLResponse:
    """返回注入统一画风后的 1v1 练习页 HTML；未构建则返回 503。"""
    index_path = _PRACTICE_LIVE_DIR / "index.html"
    if not index_path.is_file():
        return HTMLResponse(_503_HTML, status_code=503)
    html = index_path.read_text(encoding="utf-8")
    html = re.sub(
        r'<link[^>]+href="https://fonts\.googleapis\.com/css2\?[^"]*Cinzel[^"]*"[^>]*/?>\s*',
        "",
        html,
        flags=re.IGNORECASE,
    )
    # 覆盖样式走 theme.css 路由，服务端不缓存，修改 CSS 后刷新即可同步
    inject = (
        f'<link rel="stylesheet" href="{_INTER_FONT_URL}">'
        f'<link rel="stylesheet" href="{_PRACTICE_LIVE_THEME_CSS_URL}">'
    )
    if inject not in html:
        html = html.replace("</head>", inject + "\n</head>")
    return HTMLResponse(
        html,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )

@app.get("/practice/live/theme.css", response_class=Response)
async def practice_live_theme_css():
    """1v1 练习页统一画风样式表，禁止缓存，修改后刷新即生效（含从 voice_chat 跳转进入）。"""
    if not _PRACTICE_LIVE_OVERRIDE_CSS_PATH.is_file():
        return Response(status_code=404)
    body = _PRACTICE_LIVE_OVERRIDE_CSS_PATH.read_bytes()
    return Response(
        content=body,
        media_type="text/css",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/practice/live", response_class=HTMLResponse)
async def practice_live_index():
    """真人 1v1 练习页入口；从 voice_chat 跳转至 /practice/live/chat 时也返回本注入页。"""
    return _practice_live_index_response()


@app.get("/practice/live/{full_path:path}", response_class=HTMLResponse)
async def practice_live_spa(full_path: str):
    """SPA：静态资源直接返回文件；其余路径（如 /chat）均返回注入统一画风后的 index.html。"""
    if not full_path or full_path == "index.html":
        return _practice_live_index_response()
    file_path = (_PRACTICE_LIVE_DIR / full_path).resolve()
    if not str(file_path).startswith(str(_PRACTICE_LIVE_DIR.resolve())):
        return HTMLResponse("<p>Invalid path</p>", status_code=400)
    if file_path.is_file():
        return FileResponse(file_path)
    return _practice_live_index_response()


@app.get("/health")
async def health():
    """健康检查，不依赖 DB/Redis，便于 Railway 等平台判定应用已就绪"""
    return {"status": "ok", "version": VERSION}


@app.get("/", response_class=HTMLResponse)
async def server_root(request: Request):
    """默认显示语音对话页面"""
    try:
        name = getattr(configer, "default_characters", None) or "english_tutor"
        return templates.TemplateResponse("voice_chat.html", {
            "request": request,
            "character_name": name,
        })
    except Exception as e:
        logger.exception("Root template render failed: %s", e)

@app.get("/voice_chat", response_class=HTMLResponse)
async def get_voice_chat(request: Request):
    """Instagram风格的语音消息界面"""
    try:
        name = getattr(configer, "default_characters", None) or "english_tutor"
        return templates.TemplateResponse("voice_chat.html", {
            "request": request,
            "character_name": name,
        })
    except Exception as e:
        logger.exception("Voice chat template render failed: %s", e)


@app.get("/home", response_class=HTMLResponse)
async def get_home_dashboard(request: Request):
    """场景推荐主页（偏好输入 + 推荐卡片）"""
    try:
        return templates.TemplateResponse("home.html", {"request": request})
    except Exception as e:
        logger.exception("Home template render failed: %s", e)


@app.get("/user_management", response_class=HTMLResponse)
async def get_user_management(request: Request):
    """用户管理页面（仅前端入口，实际权限由接口校验）"""
    try:
        return templates.TemplateResponse("user_management.html", {"request": request})
    except Exception as e:
        logger.exception("User management template render failed: %s", e)


if __name__ == "__main__":

    import uvicorn
    uvicorn.run("main:app", host=configer.server_host, port=configer.server_port, reload=False)