# syntax=docker/dockerfile:1.7
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps: build tools for cryptography/pymysql, mysql client for CLI seeding
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      default-mysql-client \
      curl \
 && rm -rf /var/lib/apt/lists/*

# Install python deps first (layer caching)
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install -e ".[dev]"

# Copy remaining code
COPY sql ./sql
COPY scripts ./scripts
COPY tests ./tests

# Non-root user
RUN useradd --create-home --shell /bin/bash app \
 && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "storecraft.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
