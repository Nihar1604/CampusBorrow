# Official lightweight Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system runtime & build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications and install wheels
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend source files
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Pre-create instance directories and set OpenShift GID 0 permissions
RUN mkdir -p /app/backend/instance /tmp/instance && \
    chgrp -R 0 /app /tmp/instance && \
    chmod -R g=u /app /tmp/instance

# Expose backend REST & metrics ports (8080 for OpenShift, 5000 for local Docker)
EXPOSE 8080 5000

# Set production environment flags
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend
ENV PORT=8080

# Container healthcheck aligned with Kubernetes/OpenShift readiness
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8080}/api/health || exit 1

# Start CampusBorrow application via Gunicorn WSGI server
WORKDIR /app/backend
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 4 app:app"]
