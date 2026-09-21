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

# Sync dependencies into a venv at /build/.venv
RUN uv venv .venv && \
    uv pip install --no-cache -r pyproject.toml

# --- Stage 2: Runtime ---
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy only the venv from builder
COPY --from=builder /build/.venv /app/.venv

# Make venv the active Python
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source
COPY . .

# Create storage directory
RUN mkdir -p /app/storage

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
