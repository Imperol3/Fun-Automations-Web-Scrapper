# Use Python slim base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}"

# Install system dependencies required for Playwright
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Create and switch to non-root user
RUN useradd -m -u 1000 appuser
USER appuser
WORKDIR /app

# Copy requirements and install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install chromium --with-deps

# Copy application code
COPY --chown=appuser:appuser maps_scraper.py .

# Expose port
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "maps_scraper:app", "--host", "0.0.0.0", "--port", "8000"]
