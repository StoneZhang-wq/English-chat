"""MyEnglishChat 独立后端入口。"""
from __future__ import annotations

import logging

from fastapi import FastAPI

from config import SERVER_HOST, SERVER_PORT
from routers import practice_chat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MyEnglishChat API", version="0.1.0")

app.include_router(practice_chat.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
    )
