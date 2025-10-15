# DPDA Simulator Backend - FastAPI
# Multi-stage build for smaller production image

# Stage 1: Base image with dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create data directory for SQLite persistence
RUN mkdir -p /data && chmod 755 /data

# Make PATH include local packages
ENV PATH=/root/.local/bin:$PATH

# Environment variables (overridden by docker-compose)
ENV STORAGE_BACKEND=database
ENV DATABASE_URL=sqlite:////data/dpda_sessions.db
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the API server
CMD ["python", "run_api.py"]
