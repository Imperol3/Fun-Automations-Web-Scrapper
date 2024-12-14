# Google Maps Business Scraper API

A powerful Flask-based API that scrapes business information from Google Maps using Selenium. This tool provides comprehensive data extraction with real-time logging capabilities.

## Features

- 🔍 Search businesses by query and location
- 📊 Extract detailed business information:
  - Business name
  - Address
  - Phone number
  - Website
  - Rating
  - Number of reviews
  - Business hours
  - Additional details
- 📝 Real-time logging with rotating file system
- 🔒 Production-ready with Docker deployment
- 🔐 SSL/TLS support with automatic certificate renewal
- 🚀 Scalable architecture with Nginx reverse proxy

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python maps_scraper.py
```

### Docker Deployment

1. Update your domain in `nginx.conf`:
```bash
sed -i "s/YOUR_DOMAIN_NAME/yourdomain.com/g" nginx.conf
```

2. Run the deployment script:
```bash
chmod +x deploy.sh
./deploy.sh yourdomain.com
```

## API Endpoints

### Search Businesses
```http
POST /search
Content-Type: application/json

{
    "query": "restaurants",
    "location": "New York"
}
```

Response:
```json
{
    "results": [
        {
            "name": "Business Name",
            "address": "Business Address",
            "phone": "Phone Number",
            "website": "Website URL",
            "rating": "4.5",
            "reviews": "100",
            "hours": {...}
        }
    ]
}
```

## Deployment

This project includes a complete Docker setup for production deployment:

- Nginx reverse proxy with SSL/TLS
- Automatic SSL certificate renewal with Certbot
- Docker Compose for easy orchestration
- Secure configuration with non-root users
- Rotating log files

### Requirements

- Docker and Docker Compose
- Domain name pointed to your server
- Server with at least 2GB RAM

### Production Setup

1. Point your domain's A record to your server's IP
2. Clone this repository
3. Run the deployment script:
```bash
./deploy.sh yourdomain.com
```

## Logging

The scraper includes comprehensive logging:
- Real-time progress updates
- Rotating file handler to manage log sizes
- Detailed extraction information
- Error tracking and debugging info

Logs are stored in the `logs` directory with automatic rotation.

## Security

- SSL/TLS encryption
- Non-root Docker containers
- Regular security updates
- Protected API endpoints
- Secure configuration defaults

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
