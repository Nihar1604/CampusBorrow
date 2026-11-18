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

# Copy backend source files
COPY . .

# Expose backend REST & metrics port
EXPOSE 5000

# Set production environment flags
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Container healthcheck aligned with Kubernetes readiness/liveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/health || exit 1

# Start CampusBorrow application
CMD ["python", "app.py"]
