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

# Set the CMD to your handler (could be different depending on how AgentCore invokes the container)
# For standard Lambda-like invocation:
CMD ["main.handler"]
