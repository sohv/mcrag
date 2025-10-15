# MCRAG Backend API - Production Docker Image
# Multi-stage build for optimized production deployment

# Build stage - Install dependencies with UV
FROM python:3.12-slim AS builder

# Install system dependencies and UV
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install UV for fast dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache-dir -r requirements.txt

# Production stage - Minimal runtime image
FROM python:3.12-slim AS production

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash mcrag
USER mcrag
WORKDIR /home/mcrag

# Copy virtual environment from builder stage
COPY --from=builder --chown=mcrag:mcrag /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=mcrag:mcrag backend/ ./backend/
COPY --chown=mcrag:mcrag .env.example .env

# Set working directory to backend for proper imports
WORKDIR /home/mcrag/backend

# Set environment variables
ENV PYTHONPATH=/home/mcrag/backend
ENV PYTHONUNBUFFERED=1
ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# Expose port
EXPOSE 8001

# Start command
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]