# 使用轻量的 Python 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 系统依赖 - 单独一层，几乎不变，永久缓存
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# 设置 uv 安装到系统 Python（不是虚拟环境）
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

# 复制依赖文件并安装
# 注意：现在的依赖仅需 requests, streamlit 和 python-dotenv
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# 复制源代码
COPY . .

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "src/admin_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]