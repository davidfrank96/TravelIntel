FROM python:3.11-slim

WORKDIR /app

# System deps (important for selenium/playwright)
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy files
COPY . .

# Install python deps
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8501

# Start Streamlit
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
