# Google Maps Scraper API

A production-ready Flask API for scraping Google Maps search results. Built with Selenium and designed for scalability and reliability.

## Features

- Scrapes comprehensive business information from Google Maps
- Production-ready with Docker containerization
- Configurable rate limiting and timeouts
- SSL/TLS support with automatic certificate renewal
- Proper error handling and logging
- Anti-detection measures

## Prerequisites

- Docker and Docker Compose
- Domain name pointed to your server
- (Optional) Caddy server for reverse proxy

## Deployment

### Standard Deployment

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <repo-directory>
```

2. Deploy with SSL:
```bash
chmod +x deploy.sh
./deploy.sh your-domain.com
```

### Deployment with Existing Caddy Server

1. Add the Caddy configuration snippet to your Caddyfile:
```bash
cat Caddyfile.snippet >> /etc/caddy/Caddyfile
systemctl reload caddy
```

2. Deploy the application:
```bash
chmod +x deploy.sh
./deploy.sh your-domain.com
```

## API Usage

### Scrape Google Maps Results

```bash
curl -X POST https://your-domain.com/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "restaurants in new york",
    "limit": 30
  }'
```

Response format:
```json
{
  "status": "success",
  "search_query": "restaurants in new york",
  "results_count": 30,
  "results": [
    {
      "name": "Restaurant Name",
      "rating": "4.5",
      "reviews": "1,234 reviews",
      "address": "123 Main St, New York, NY",
      "phone": "+1 234-567-8900",
      "website": "https://example.com",
      "category": "Restaurant"
    }
  ],
  "message": "Scraping completed successfully"
}
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:
```env
FLASK_ENV=production
FLASK_APP=maps_scraper.py
```

### Timeouts

- API timeout: 180 seconds
- Scraping timeout: 180 seconds
- Individual request timeout: 30 seconds

## Maintenance

### Viewing Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f web
docker-compose logs -f nginx
```

### Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker-compose down
docker-compose up -d --build
```

## Security

- Runs as non-root user
- SSL/TLS encryption
- Rate limiting
- Input validation
- Anti-bot detection measures

## License

[Your License]
