# Use the official Playwright image which includes all dependencies
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PATH="/home/pwuser/.local/bin:${PATH}"

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY maps_scraper.py .

# Expose port
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "maps_scraper:app", "--host", "0.0.0.0", "--port", "8000"]
