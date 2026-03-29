#!/usr/bin/env python3
"""云平台启动入口：从环境变量 PORT 读取端口并启动 uvicorn（Railway / Heroku 等）"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
