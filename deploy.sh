#!/bin/bash

# Replace YOUR_DOMAIN_NAME with actual domain
if [ -z "$1" ]; then
    echo "Please provide your domain name as an argument"
    echo "Usage: ./deploy.sh yourdomain.com"
    exit 1
fi

DOMAIN=$1

# Create required directories
mkdir -p certbot/conf certbot/www

# Update nginx.conf with domain name
sed -i "s/YOUR_DOMAIN_NAME/$DOMAIN/g" nginx.conf

# Start containers
docker-compose up -d nginx
docker-compose up certbot

# Get SSL certificate
docker-compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot/ --email your-email@example.com --agree-tos --no-eff-email -d $DOMAIN

# Restart nginx to load SSL certificate
docker-compose restart nginx
