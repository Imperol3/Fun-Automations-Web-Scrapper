# Use Python slim base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create and switch to non-root user
RUN useradd -m -u 1000 appuser
USER appuser
WORKDIR /app

# Copy requirements and install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install chromium --with-deps

# Copy application code
COPY --chown=appuser:appuser maps_scraper.py .

# Expose port
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "maps_scraper:app", "--host", "0.0.0.0", "--port", "8000"]
