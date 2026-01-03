FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /var/task

# 非rootユーザーを作成
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --no-create-home appuser

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev && \
    chown -R appuser:appuser /var/task

# Place executables in the environment at the front of the path
ENV PATH="/var/task/.venv/bin:$PATH"

COPY --chown=appuser:appuser app/ ./app/

# 非rootユーザーに切り替え
USER appuser

# Expose port for HTTP server
EXPOSE 8080

# ヘルスチェック（30秒ごとに/pingを確認）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/ping')" || exit 1

# Start the FastAPI server with Uvicorn
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
