FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /var/task

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/var/task/.venv/bin:$PATH"

COPY app/ .

# Expose port for HTTP server
EXPOSE 8080

# Start the FastAPI server with Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
