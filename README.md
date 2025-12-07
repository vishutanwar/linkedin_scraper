# LinkedIn Scraper API

A FastAPI REST API service for scraping LinkedIn posts from search results. Extracts post text, job application links, profile links, images, and poster names.

## Features

- ✅ **REST API** - Easy-to-use HTTP API with Swagger documentation
- ✅ **Docker Support** - Containerized deployment with Docker Compose
- ✅ **Proxy Support** - Configure proxies to avoid IP blocking
- ✅ **Cookie Authentication** - Uses browser cookies for LinkedIn login
- ✅ **Dynamic Scrolling** - Automatically scrolls to load more posts
- ✅ **Comprehensive Data** - Extracts text, images, profile links, and more
- ✅ **Production Ready** - Includes health checks, error handling, and logging

## Quick Start

### Using Docker (Recommended)

```bash
# 1. Clone repository
git clone <your-repo-url>
cd linkedin_scraper

# 2. Add your LinkedIn cookies
# Create linkedin_cookies.json with your cookies (see Setup Guide)

# 3. Configure environment
cp env.example .env
# Edit .env and set your API key

# 4. Build and start
docker-compose build
docker-compose up -d

# 5. Test
curl http://localhost:8000/health
```

### Using Python

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set API key
export LINKEDIN_SCRAPER_API_KEY="your-api-key"

# Start server
uvicorn api:app --host 0.0.0.0 --port 8000
```

## API Usage

### Authentication

All requests require an API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/scrape
```

### Scrape LinkedIn Posts

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.linkedin.com/search/results/content/?keywords=n8n",
    "max_scroll": 5,
    "scroll_delay": 2
  }'
```

### With Proxy

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.linkedin.com/search/results/content/?keywords=n8n",
    "max_scroll": 5,
    "scroll_delay": 2,
    "proxy": {
      "server": "http://proxy-server:port"
    }
  }'
```

### Python Example

```python
import requests

response = requests.post(
    'http://localhost:8000/scrape',
    headers={
        'X-API-Key': 'your-api-key',
        'Content-Type': 'application/json'
    },
    json={
        'url': 'https://www.linkedin.com/search/results/content/?keywords=n8n',
        'max_scroll': 5,
        'scroll_delay': 2,
        'proxy': {
            'server': 'http://proxy-server:port'  # Optional
        }
    }
)

result = response.json()
print(f"Found {result['count']} posts")
for post in result['posts']:
    print(f"- {post['name']}: {post['text'][:100]}...")
```

## API Endpoints

### POST `/scrape`

Scrape LinkedIn posts from a search results URL.

**Request Body:**
```json
{
  "url": "https://www.linkedin.com/search/results/content/?keywords=n8n",
  "max_scroll": 5,
  "scroll_delay": 2,
  "headless": false,
  "cookies_file": "linkedin_cookies.json",
  "proxy": {
    "server": "http://proxy-server:port",
    "username": "optional",
    "password": "optional"
  }
}
```

**Response:**
```json
{
  "success": true,
  "posts": [
    {
      "text": "Post content...",
      "name": "John Doe",
      "profile_link": "https://www.linkedin.com/in/johndoe",
      "job_application_link": "https://www.linkedin.com/jobs/view/123",
      "image_links": ["https://media.licdn.com/..."]
    }
  ],
  "count": 1,
  "message": "Successfully scraped 1 posts"
}
```

### GET `/health`

Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "service": "LinkedIn Scraper API",
  "version": "1.0.0",
  "authentication": "enabled"
}
```

## Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc
- **Setup Guide**: See [SETUP.md](SETUP.md) for detailed deployment instructions

## Configuration

### Environment Variables

Create a `.env` file (copy from `env.example`):

```bash
LINKEDIN_SCRAPER_API_KEY=your-strong-random-api-key
LINKEDIN_SCRAPER_AUTH_ENABLED=true
```

### Cookies File

The API uses `linkedin_cookies.json` for LinkedIn authentication. This file must be present in the application directory.

**How to get cookies:**
1. Log in to LinkedIn in your browser
2. Use a browser extension like "Cookie Editor" to export cookies as JSON
3. Save as `linkedin_cookies.json` in the project root

## Project Structure

```
linkedin_scraper/
├── api.py                 # FastAPI application
├── linkedin_scraper.py    # Scraper logic
├── scrape_worker.py       # Worker subprocess script
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose configuration
├── .dockerignore        # Docker ignore rules
├── .gitignore          # Git ignore rules
├── env.example         # Environment variables template
├── README.md           # This file
└── SETUP.md            # Detailed setup guide
```

## Requirements

- Python 3.9+
- Docker & Docker Compose (for containerized deployment)
- Playwright browsers (installed automatically in Docker)
- LinkedIn account with valid cookies

## Important Notes

- **Cookies**: Must be valid and up-to-date. Update `linkedin_cookies.json` when cookies expire.
- **Rate Limiting**: Be respectful of LinkedIn's servers. Don't scrape too aggressively.
- **Terms of Service**: Ensure your usage complies with LinkedIn's Terms of Service.
- **Proxy**: Using a proxy is recommended for production to avoid IP blocking.
- **Security**: Always use strong API keys and HTTPS in production.

## Troubleshooting

### No Posts Found

1. Check logs: `docker-compose logs -f | grep SCRAPER`
2. Verify cookies are valid and not expired
3. Check if LinkedIn is blocking (look for login/challenge pages in logs)
4. Try using a proxy

### Container Issues

```bash
# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Playwright Issues

```bash
# Reinstall browsers
docker exec linkedin-scraper-api playwright install chromium
```

For more troubleshooting, see [SETUP.md](SETUP.md).

## License

This project is for educational purposes. Use responsibly and in accordance with LinkedIn's Terms of Service.
