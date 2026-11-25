# Multi-stage build for RetinaSahayak Backend (Python 3.11/3.12/3.13 compatible)
FROM python:3.11-slim

# Prevent Python from writing .pyc and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install system dependencies for OpenCV and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend ./backend

# Create storage directory structure
RUN mkdir -p /app/backend/storage/raw_images \
             /app/backend/storage/enhanced \
             /app/backend/storage/heatmaps \
             /app/backend/storage/overlays \
             /app/backend/storage/reports

EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
