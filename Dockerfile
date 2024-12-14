# Use multi-stage build for smaller final image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome and dependencies in final image
FROM python:3.11-slim

# Copy Chrome repository signing key from builder
COPY --from=builder /usr/bin/wget /usr/bin/wget
COPY --from=builder /usr/bin/gpg /usr/bin/gpg

# Install Chrome and required dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    curl \
    unzip \
    xvfb \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | awk -F'.' '{print $1}') \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") \
    && wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip -d /usr/local/bin \
    && rm chromedriver_linux64.zip \
    && chmod +x /usr/local/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV FLASK_ENV=production
ENV GUNICORN_CMD_ARGS="--workers=2 --threads=4 --timeout=300 --bind=0.0.0.0:5000"

# Expose port
EXPOSE 5000

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Start Xvfb and run the application with proper error handling
CMD sh -c "Xvfb :99 -screen 0 1920x1080x16 & gunicorn maps_scraper:app"
