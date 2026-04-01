<<<<<<< HEAD
# Use official Playwright image (includes Python + browsers)
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Prevent Python issues
=======
﻿# TravelIntel Briefing API Dockerfile
FROM python:3.11-slim

>>>>>>> 5bf608d (code update)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

<<<<<<< HEAD
# Copy requirements first (cache optimization)
=======
WORKDIR /app

# System deps (minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

>>>>>>> 5bf608d (code update)
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

<<<<<<< HEAD
# Copy application
COPY . .

# Create persistence directories
RUN mkdir -p /app/data /app/models

# Expose Streamlit
EXPOSE 8501

# Default command (overridden by docker-compose)
CMD ["python", "main.py"]
=======
COPY . .

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "-m", "briefing.run_api"]
>>>>>>> 5bf608d (code update)
