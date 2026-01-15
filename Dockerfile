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
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first for better caching
COPY requirements.txt .

# Install PyTorch CPU version first (much faster, ~70% smaller)
RUN pip install --no-cache-dir \
    torch==2.6.0 \
    torchaudio==2.6.0 \
    torchvision==0.21.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
RUN pip install --no-cache-dir \
    -r requirements.txt \
    git+https://github.com/descriptinc/audiotools@348ebf2034ce24e2a91a553e3171cb00c0c71678

# Install Playwright browsers (only once with deps, chromium only for smaller size)
RUN playwright install --with-deps chromium

# Optionally, if you use chromium only:
# RUN playwright install chromium
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
