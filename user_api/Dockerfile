# Dockerfile
FROM python:3.12.3-slim

WORKDIR /app

# 装到系统级 Python，不建虚拟环境 + 预编译字节码加速启动
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
ENV UV_COMPILE_BYTECODE=1

# 先复制依赖文件（利用 Docker 缓存层，代码变了不用重装依赖）
COPY pyproject.toml .
COPY uv.lock .
RUN pip install --no-cache-dir uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev


# 复制项目代码
COPY . .