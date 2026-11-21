# ZetaGram Telegram Bot Dockerfile
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL="sqlite+aiosqlite:////app/data/bot.db" \
    PERSISTENCE_FILE="/app/data/bot_persistence.pickle"

WORKDIR /app

# Install system essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project source code
COPY . .

# Create persistent storage directory and run as non-root user
RUN mkdir -p /app/data && \
    useradd -u 1000 -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

VOLUME ["/app/data"]

CMD ["python", "main.py"]
