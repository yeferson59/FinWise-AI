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

# Install uv - fast Python package installer
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
FROM python:3.13-slim

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

# Create non-root user for security with home directory
# Running as non-root reduces attack surface
RUN groupadd -r appuser && useradd -r -g appuser -u 1001 -m -d /home/appuser appuser

# Set working directory
WORKDIR /app

# Create necessary directories
# - /app/uploads: for user uploaded files
# - /app/data: for SQLite database file (needs write permissions for appuser)
# - /tmp/numba_cache: for Numba JIT compilation cache
# - /home/appuser/.cache: for Hugging Face, transformers, and other Python libraries
RUN mkdir -p /app/uploads \
  /app/data \
  /tmp/numba_cache \
  /home/appuser/.cache/huggingface \
  /home/appuser/.cache/torch \
  /home/appuser/.cache/pip

# Copy Python dependencies from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app ./app
COPY pyproject.toml ./

# Copy entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set ownership of ALL directories and files to appuser
# This must be done AFTER all COPY operations to ensure correct permissions
RUN chown -R appuser:appuser /app /home/appuser /tmp/numba_cache

# NOTE: We do NOT switch to non-root user here because Docker volumes
# mounted at runtime (like /app/data) may have root ownership.
# The entrypoint script will fix permissions and then switch to appuser.
# USER appuser

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Environment variables for production
# These can be overridden at runtime
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  NUMBA_CACHE_DIR=/tmp/numba_cache \
  HF_HOME=/home/appuser/.cache/huggingface \
  TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface/transformers \
  TORCH_HOME=/home/appuser/.cache/torch \
  XDG_CACHE_HOME=/home/appuser/.cache \
  HOME=/home/appuser \
  PORT=8000

# Expose the application port
EXPOSE 8000

# Health check to ensure the container is running correctly
# Checks the /health endpoint every 30 seconds
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/').read()"

# Set entrypoint to our initialization script
# The script will verify directories, permissions, and environment variables
# before starting the application
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
# The entrypoint script will handle starting uvicorn
CMD []

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
#     -e DATABASE_URL="sqlite:////app/data/database.db" \
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
# Important Notes:
#   - SQLite URL must use 4 slashes: sqlite:////app/data/database.db
#   - The /app/data directory has write permissions for appuser
#   - All cache directories are properly configured for ML libraries
#
# =============================================================================
