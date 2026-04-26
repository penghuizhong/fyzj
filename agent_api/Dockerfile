# ==========================================
# 方圆智版 Agent 服务 - 生产环境 Dockerfile
# ==========================================
FROM python:3.12.3-slim

# 设置工作目录
WORKDIR /app

# ── 1. 环境变量设置 ─────────────────────────────────────────
# PYTHONUNBUFFERED: 让日志实时输出，不被缓冲拦截
# PYTHONPATH: 极其关键！让 Python 能直接识别 src 目录下的包（例如直接 import core 而不是 src.core）
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/src:/app" \
    UV_PROJECT_ENVIRONMENT="/usr/local/" \
    UV_COMPILE_BYTECODE=1

# ── 2. 安装 uv ─────────────────────────────────
RUN pip install --no-cache-dir uv

# ── 3. 安装依赖 (利用 Docker 缓存层) ────────────────────────
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ── 4. 复制代码 ─────────────────────────────────────────────
# 这里假设您已经配置好了 .dockerignore (忽略了 .env, .venv 等)
COPY . .

# ── 5. 暴露端口与启动 ───────────────────────────────────────
# 按照咱们之前的极简架构约定，Agent 引擎独立运行在 8001 端口
EXPOSE 8001

CMD ["python", "src/main.py"]