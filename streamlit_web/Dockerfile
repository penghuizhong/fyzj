# 使用轻量的 Python 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装必要的系统工具（如 curl 用于健康检查）
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
# 注意：现在的依赖仅需 requests, streamlit 和 python-dotenv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 启动命令
# 建议以 ingest_ui.py 为主入口
CMD ["streamlit", "run", "src/ingest_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]