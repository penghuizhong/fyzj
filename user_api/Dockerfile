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
COPY src/agents/ ./agents/
COPY src/core/ ./core/
COPY src/memory/ ./memory/
COPY src/schema/ ./schema/
COPY src/service/ ./service/
COPY src/scripts/ ./scripts/
COPY src/tasks/ ./tasks/
COPY src/models/ ./models/
COPY src/run_service.py .
COPY ./config.yaml .

# 复制数据文件
COPY data/ ./data/

# 复制 alembic 配置（用于数据库迁移）
COPY alembic.ini .
COPY alembic/ ./alembic/

EXPOSE 8000

# 直接用 python，不需要 uv run（因为已装到系统级）
CMD ["python", "run_service.py"]