# English-Chat 应用镜像
FROM python:3.11-slim

WORKDIR /app

# pydub 依赖 ffmpeg/ffprobe 做 TTS 音频转换
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg && rm -rf /var/lib/apt/lists/*

# 先安装依赖，利用层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 应用代码
COPY . .

# 日志与数据目录（与 config 中的路径一致时可挂载）
RUN mkdir -p /app/logs /app/data /app/frontend/static/images/scenes

# 非 root 运行（可选）
# RUN adduser --disabled-password appuser && chown -R appuser:appuser /app
# USER appuser

EXPOSE 8080

# Railway 等平台注入 PORT，run.py 会读取并监听该端口
CMD ["python", "run.py"]
