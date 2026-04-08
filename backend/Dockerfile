# Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create log directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 5010

# Set environment variables
ENV FLASK_ENV=production
ENV PORT=5010
ENV HOST=0.0.0.0
ENV LOG_FOLDER=/app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5010/health').read()" || exit 1

# Run with gunicorn for production
# Note: For Windows-specific features (GPU monitoring), you may need to run this on Windows
# or modify the GPU detection to work in Linux containers
CMD ["gunicorn", "--config", "gunicorn_config.py", "sys_logger:app"]

