#!/bin/bash

# Exit on error
set -e

echo "Deploying FastAPI Google Maps Scraper..."

# Pull latest changes
git pull

# Stop any running containers
docker-compose down

# Build and start the new container
docker-compose up --build -d

echo "Deployment completed! Your application should be running on port 8080"
echo "Check the logs with: docker-compose logs -f"
echo "Test the API with: curl -X POST http://localhost:8080/scrape -H 'Content-Type: application/json' -d '{\"search_query\": \"restaurants in new york\", \"limit\": 5}'"
