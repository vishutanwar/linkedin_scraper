# Testing Guide for LinkedIn Scraper API

## Quick Start

The Docker container is now running! Here's how to test it:

## 1. Check Container Status

```bash
docker ps | grep linkedin-scraper-api
```

You should see the container running and healthy.

## 2. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
    "status": "healthy",
    "service": "LinkedIn Scraper API",
    "version": "1.0.0",
    "authentication": "enabled"
}
```

## 3. Test Scrape Endpoint

### Using curl:

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: Playindark-andstayalive-22-bye" \
  -d '{
    "url": "https://www.linkedin.com/search/results/content/?keywords=python",
    "max_scroll": 2,
    "scroll_delay": 2,
    "headless": true
  }'
```

### Using the test script:

```bash
./test_api.sh
```

### Using Python:

```python
import requests

api_key = "Playindark-andstayalive-22-bye"
url = "http://localhost:8000/scrape"

response = requests.post(
    url,
    headers={
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    },
    json={
        "url": "https://www.linkedin.com/search/results/content/?keywords=python",
        "max_scroll": 2,
        "scroll_delay": 2,
        "headless": True
    }
)

print(response.json())
```

## 4. Monitor Logs

### View all logs:
```bash
docker logs linkedin-scraper-api
```

### Follow logs in real-time:
```bash
docker logs -f linkedin-scraper-api
```

### View last 50 lines:
```bash
docker logs --tail 50 linkedin-scraper-api
```

## 5. Test with Swagger UI

Open your browser and go to:
```
http://localhost:8000/docs
```

This will show the interactive API documentation where you can test endpoints directly.

**Note:** Make sure to:
1. Click "Authorize" button at the top
2. Enter your API key: `Playindark-andstayalive-22-bye`
3. Then try the `/scrape` endpoint

## Important Notes

1. **Cookies File**: The API uses `linkedin_cookies.json` from your local directory. Make sure it's valid and up-to-date.

2. **API Key**: The default API key is `Playindark-andstayalive-22-bye`. You can change it by setting the `LINKEDIN_SCRAPER_API_KEY` environment variable.

3. **Scraping Time**: Scraping can take 1-5 minutes depending on `max_scroll` and `scroll_delay` parameters.

4. **Headless Mode**: In Docker, headless mode is automatically enabled (even if you set `headless: false`).

## Troubleshooting

### Container not starting:
```bash
docker logs linkedin-scraper-api
```

### Check if cookies file is mounted:
```bash
docker exec linkedin-scraper-api ls -la /app/linkedin_cookies.json
```

### Restart container:
```bash
docker-compose restart
```

### Stop container:
```bash
docker-compose down
```

### Rebuild and restart:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Example Response

A successful scrape will return:

```json
{
  "success": true,
  "posts": [
    {
      "text": "Post content here...",
      "name": "John Doe",
      "profile_link": "https://www.linkedin.com/in/johndoe",
      "job_application_link": "...",
      "image_links": []
    }
  ],
  "count": 1,
  "message": "Scraping completed successfully"
}
```

