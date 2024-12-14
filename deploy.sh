#!/bin/bash

# Exit on error
set -e

# Check if domain argument is provided
if [ -z "$1" ]; then
    echo "Please provide your domain name as an argument"
    echo "Usage: ./deploy.sh yourdomain.com"
    exit 1
fi

DOMAIN=$1

# Create required directories
mkdir -p certbot/conf
mkdir -p certbot/www

# Stop any running containers
docker-compose down

# Start nginx container
docker-compose up --force-recreate -d nginx

# Wait for nginx to start
sleep 5

# Get SSL certificate
docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot \
    --email admin@${DOMAIN} --agree-tos --no-eff-email \
    -d ${DOMAIN}

# Restart containers
docker-compose down
docker-compose up -d

echo "Deployment completed! Your application should be running at https://${DOMAIN}"
echo "Check the logs with: docker-compose logs -f"
