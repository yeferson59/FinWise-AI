# =============================================================================
# Multi-stage Dockerfile for FinWise-AI Backend
# Optimized for production: minimal size, fast startup, secure
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and build environment
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# Install system dependencies required for building Python packages
# These include compilers, headers, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  g++ \
  build-essential \
  libgomp1 \
  && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first (better caching)
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv (much faster than pip)
# --no-dev: exclude development dependencies
# --frozen: use exact versions from uv.lock
# Increase timeout and add retry for network issues
ENV UV_HTTP_TIMEOUT=300
RUN uv sync --frozen --no-dev --no-install-project

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# -----------------------------------------------------------------------------
FROM builder

# Install runtime system dependencies
# Tesseract OCR with English and Spanish language packs
# Libraries required by OpenCV and other image processing tools
RUN apt-get update && apt-get install -y --no-install-recommends \
  tesseract-ocr \
  tesseract-ocr-eng \
  tesseract-ocr-spa \
  libglib2.0-0 \
  libsm6 \
  libxext6 \
  libxrender-dev \
  libgomp1 \
  libgl1 \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
# Running as non-root reduces attack surface
RUN groupadd -r appuser && useradd -r -g appuser -u 1001 -m -d /home/appuser appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser pyproject.toml ./

# Create uploads directory with proper permissions
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

# Create data directory for SQLite database with proper permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

RUN mkdir -p /app/cache && chown -R appuser:appuser /app/cache

# Create numba cache directory to fix caching issues with Python 3.13
RUN mkdir -p /tmp/numba_cache && chmod -R 777 /tmp/numba_cache

# Create Hugging Face cache directories with proper permissions
RUN mkdir -p /home/appuser/.cache/huggingface && \
  chown -R appuser:appuser /home/appuser/.cache

# Switch to non-root user
USER appuser

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Environment variables for production
# These can be overridden at runtime
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PORT=8000 \
  NUMBA_CACHE_DIR=/tmp/numba_cache \
  HF_HOME=/home/appuser/.cache/huggingface \
  TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface \
  HUGGINGFACE_HUB_CACHE=/home/appuser/.cache/huggingface

# Expose the application port
EXPOSE 8000

# Health check to ensure the container is running correctly
# Checks the /health endpoint every 30 seconds
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/').read()"

# Run the application with uvicorn
# Using 0.0.0.0 to listen on all interfaces (required in containers)
# --host 0.0.0.0: bind to all network interfaces
# --port: configurable via PORT env var
# --workers 1: single worker by default (scale with container replicas)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]

# =============================================================================
# Build and Run Instructions:
# =============================================================================
#
# Build the image:
#   docker build -t finwise-backend:latest .
#
# Run the container:
#   docker run -d \
#     -p 8000:8000 \
#     -e SECRET_KEY="your-secret-key-min-32-chars" \
#     -e OPENAI_API_KEY="your-api-key" \
#     -e DATABASE_URL="sqlite:///database.db" \
#     -e ALGORITHM="HS256" \
#     -v finwise-uploads:/app/uploads \
#     -v finwise-data:/app/data \
#     --name finwise-backend \
#     finwise-backend:latest
#
# Environment Variables (Required):
#   - SECRET_KEY: JWT signing key (minimum 32 characters)
#   - OPENAI_API_KEY: OpenRouter or OpenAI API key
#   - DATABASE_URL: Database connection string
#   - ALGORITHM: JWT algorithm (default: HS256)
#
# Optional Environment Variables:
#   - PORT: Server port (default: 8000)
#   - ACCESS_TOKEN_EXPIRE_MINUTES: Token lifetime (default: 30)
#   - MODELS: AI model to use (default: nvidia/llama-3.3-nemotron-70b-instruct)
#   - TEMPERATURE: LLM temperature (default: 0.2)
#   - TOP_P: LLM top-p sampling (default: 0.3)
#   - FILE_STORAGE_TYPE: 'local' or 's3' (default: local)
#   - LOCAL_STORAGE_PATH: Upload directory (default: uploads)
#
# Volume Mounts:
#   - /app/uploads: For persistent file storage
#   - /app/data: For SQLite database (if using SQLite)
#
# For PostgreSQL (recommended for production):
#   docker run -d \
#     -e DATABASE_URL="postgresql://user:password@db-host:5432/finwise" \
#     ...
#
# =============================================================================
