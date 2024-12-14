# Google Maps Scraper API

A production-ready API service for scraping business information from Google Maps.

## API Endpoints

### POST /scrape
Scrapes business information from Google Maps based on a search query.

**Request Body:**
```json
{
    "search_query": "restaurants in new york",
    "limit": 5
}
```

**Response:**
```json
{
    "status": "success",
    "results": [
        {
            "name": "Business Name",
            "rating": "4.5",
            "reviews": "123",
            "category": "Restaurant",
            "address": "123 Main St, New York, NY",
            "phone": "+1 234-567-8900",
            "website": "https://example.com"
        }
    ]
}
```

## Usage Example

```bash
curl -X POST https://gmb-scraper.funautomations.io/scrape \
  -H "Content-Type: application/json" \
  -d '{"search_query": "restaurants in new york", "limit": 5}'
```

## Deployment

1. Clone the repository
2. Update environment variables if needed
3. Run with Docker Compose:
```bash
docker-compose up -d
```

## Environment Variables
- `FLASK_ENV`: Set to 'production' for production mode
- `FLASK_APP`: Set to 'maps_scraper.py'

## Notes
- This is an API-only service designed for production use
- Implements rate limiting and error handling
- Uses Chrome in headless mode for scraping
