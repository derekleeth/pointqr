# =============================================================================
# PointQR Backend – Multi-stage Dockerfile
# =============================================================================

# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv==0.4.29

# Copy dependency files
COPY pyproject.toml ./
# Create a minimal README so uv/pip doesn't complain
RUN touch README.md

# Sync dependencies into a venv at /opt/venv (outside /app so dev bind mounts can't shadow it)
RUN uv venv /opt/venv && \
    uv pip install --no-cache -r pyproject.toml --python /opt/venv/bin/python

# --- Stage 2: Runtime ---
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy venv from builder – lives at /opt/venv, safe from any /app bind mounts
COPY --from=builder /opt/venv /opt/venv

# Make venv the active Python
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

# Copy application source
COPY . .

# Create storage directory
RUN mkdir -p /app/storage

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
