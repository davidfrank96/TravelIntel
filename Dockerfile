# Use official Playwright image (includes Python + browsers)
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Prevent Python issues
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Copy requirements first (cache optimization)
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create persistence directories
RUN mkdir -p /app/data /app/models

# Expose Streamlit
EXPOSE 8501

# Default command (overridden by docker-compose)
CMD ["python", "main.py"]
