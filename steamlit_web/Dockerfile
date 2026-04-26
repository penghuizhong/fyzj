FROM python:3.12.3-slim

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml .
COPY uv.lock .
RUN pip install --no-cache-dir uv

# Install only the dependencies needed for the client application
# --frozen: Use exact versions from the lock file
# --only-group client: Only install dependencies marked as part of the "client" group in pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --only-group client

COPY src/core/ ./core/
COPY data/ ./data/
COPY src/scripts/ ./scripts/
COPY src/schema/ ./schema/
COPY src/pages/ ./pages/
COPY src/streamlit_admin.py .

CMD ["streamlit", "run", "streamlit_admin.py"]
