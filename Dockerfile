FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (without the project itself)
RUN uv sync --frozen --no-install-project

# Copy source code
COPY src/ src/

# Install the project
RUN uv sync --frozen

FROM python:3.12-slim

WORKDIR /app

# Copy the entire virtual environment and project from builder
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

ENTRYPOINT ["mcp-privilege-cloud"]
