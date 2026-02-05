# Use Python 3.11 slim as base image
FROM python:3.11

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    libpq-dev \
    gcc \
    python3-dev \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    postgresql-client \
    # Playwright/Chromium dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    fonts-liberation \
    fonts-unifont \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first for better caching
COPY requirements_minimal.txt .

# Install PyTorch CPU version first (much faster, ~70% smaller)
RUN pip install --no-cache-dir \
    torch==2.6.0 \
    torchaudio==2.6.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
RUN pip install --no-cache-dir -r requirements_minimal.txt

# Install Playwright browsers (chromium only for smaller image)
# Dependencies are already installed above, so we don't need --with-deps
RUN playwright install chromium
# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/notifications/logs \
    /app/notifications/daily \
    /app/notifications/weekly

# Set permissions
RUN chmod +x /app/notifications/run_notifications.sh

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "--workers", "2", "--timeout", "300", "--bind", "0.0.0.0:8000", "My_AI_Guruji.wsgi:application"]
