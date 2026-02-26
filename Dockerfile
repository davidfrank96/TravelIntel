FROM python:3.11-slim

# Prevent .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    unzip \
    build-essential \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better Docker caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Copy entire project
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
