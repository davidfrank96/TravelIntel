# Use the official Playwright image which includes Python and browsers
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories for data persistence
RUN mkdir -p data/wordlists models

# Set python path
ENV PYTHONPATH=/app

# Default command (overridden in docker-compose)
CMD ["python", "main.py"]