# LinkedIn Scraper API

A FastAPI REST API service for scraping LinkedIn posts from search results. Extracts post text, job application links, profile links, images, and poster names.

## 🚀 Quick Deployment

See [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) for quick deployment steps, or [DEPLOY.md](DEPLOY.md) for detailed instructions.

## Features

- Scrapes LinkedIn posts from search results URLs
- Extracts:
  - Post text content
  - Job application links (if available)
  - Profile link of the poster
  - Image links (if available)
  - Name of the poster
- Uses browser cookies for authentication
- Exports data to JSON format
- Handles dynamic content loading with scrolling

## Installation

### Step 1: Create a Virtual Environment

It's recommended to use a virtual environment to avoid affecting your system Python installation.

**On macOS/Linux:**
```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

**On Windows (Command Prompt):**
```cmd
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate.bat
```

**On Windows (PowerShell):**
```powershell
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\Activate.ps1
```

**Note:** If you get an execution policy error in PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

### Step 2: Install Python Dependencies

With the virtual environment activated, install the required packages:
```bash
pip install -r requirements.txt
```

### Step 3: Install Playwright Browsers

Install the Chromium browser for Playwright:
```bash
playwright install chromium
```

### Step 4: Deactivate Virtual Environment (when done)

When you're finished working, you can deactivate the virtual environment:
```bash
deactivate
```

**Note:** Remember to activate the virtual environment each time you want to use the scraper:
- macOS/Linux: `source venv/bin/activate`
- Windows CMD: `venv\Scripts\activate.bat`
- Windows PowerShell: `venv\Scripts\Activate.ps1`

## Getting LinkedIn Cookies

You need to export cookies from your browser after logging into LinkedIn. Here are methods for different browsers:

### Chrome/Edge (Using Browser Extension)

1. Install a cookie export extension like "Cookie Editor" or "Get cookies.txt LOCALLY"
2. Go to LinkedIn and log in
3. Export cookies as JSON
4. Save the file (e.g., `linkedin_cookies.json`)

### Manual Cookie Extraction

1. Log in to LinkedIn in your browser
2. Open Developer Tools (F12)
3. Go to Application/Storage tab → Cookies → https://www.linkedin.com
4. Copy relevant cookies (especially `li_at`, `JSESSIONID`, `bcookie`, etc.)
5. Create a JSON file with this format:

```json
[
  {
    "name": "li_at",
    "value": "your_li_at_cookie_value",
    "domain": ".linkedin.com",
    "path": "/",
    "expires": -1,
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
  },
  {
    "name": "JSESSIONID",
    "value": "your_jsessionid_value",
    "domain": ".linkedin.com",
    "path": "/",
    "expires": -1,
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
  }
]
```

### Using the Cookie Helper Script

You can use the provided `extract_cookies.py` script to extract cookies from your browser:

```bash
python extract_cookies.py
```

Follow the instructions to export cookies from your browser.

## Usage

### Basic Usage

```bash
python linkedin_scraper.py "https://www.linkedin.com/search/results/content/?datePosted=%22past-24h%22&keywords=(%23n8n%20AND%20(%23hiring%20OR%20hiring))%20OR%20(%22workflow%20automations%22)&origin=GLOBAL_SEARCH_HEADER&sid=p2E" --cookies linkedin_cookies.json
```

### Advanced Options

```bash
python linkedin_scraper.py <URL> \
  --cookies linkedin_cookies.json \
  --output output.json \
  --scrolls 10 \
  --scroll-delay 3
```

### Arguments

- `url` (required): LinkedIn search results URL
- `--cookies`, `-c`: Path to JSON file containing cookies
- `--output`, `-o`: Output JSON filename (default: `linkedin_posts.json`)
- `--scrolls`, `-s`: Number of scrolls to load more posts (default: 5)
- `--scroll-delay`, `-d`: Delay between scrolls in seconds (default: 2)
- `--headless`: Run browser in headless mode (default: visible window to avoid detection)

## Output Format

The scraper outputs a JSON file with the following structure:

```json
[
  {
    "text": "Post content text here...",
    "name": "John Doe",
    "profile_link": "https://www.linkedin.com/in/johndoe",
    "job_application_link": "https://www.linkedin.com/jobs/view/123456",
    "image_links": [
      "https://media.licdn.com/dms/image/..."
    ]
  },
  {
    "text": "Another post...",
    "name": "Jane Smith",
    "profile_link": "https://www.linkedin.com/in/janesmith",
    "job_application_link": "",
    "image_links": []
  }
]
```

## Example

```bash
# Scrape posts with default settings
python linkedin_scraper.py "https://www.linkedin.com/search/results/content/?keywords=python" --cookies cookies.json

# Scrape with more scrolls and custom output
python linkedin_scraper.py "https://www.linkedin.com/search/results/content/?keywords=python" \
  --cookies cookies.json \
  --output my_posts.json \
  --scrolls 15 \
  --scroll-delay 2

# Run in headless mode (default is visible window)
python linkedin_scraper.py "https://www.linkedin.com/search/results/content/?keywords=python" \
  --cookies cookies.json \
  --headless
```

## API Usage

The scraper can also be run as a REST API service using FastAPI. This allows you to deploy it on a server and make HTTP requests to scrape LinkedIn posts.

### Starting the API Server

```bash
# Activate virtual environment first
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Set your API key (optional, defaults to "your-secret-api-key-change-this")
export LINKEDIN_SCRAPER_API_KEY="your-secret-api-key-here"

# Start the API server
python api.py
```

Or using uvicorn directly:

```bash
# Set API key
export LINKEDIN_SCRAPER_API_KEY="your-secret-api-key-here"

# Start server
uvicorn api:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. You can access:
- API documentation: `http://localhost:8000/docs` (Swagger UI)
- Alternative docs: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

### Authentication

The API uses API key authentication for security. All requests to the `/scrape` endpoint require a valid API key in the `X-API-Key` header.

**Configuration:**
- Set the `LINKEDIN_SCRAPER_API_KEY` environment variable to your desired API key
- Default API key is `your-secret-api-key-change-this` (change this in production!)
- To disable authentication for development, set `LINKEDIN_SCRAPER_AUTH_ENABLED=false`

**Note:** The `/health` endpoint does not require authentication.

### API Endpoints

#### POST `/scrape`

Scrape LinkedIn posts from a given URL.

**Authentication:** Required - Include `X-API-Key` header with your API key.

**Request Headers:**
- `X-API-Key`: Your API key (required)
- `Content-Type`: `application/json`

**Request Body:**
```json
{
  "url": "https://www.linkedin.com/search/results/content/?keywords=python",
  "max_scroll": 5,
  "scroll_delay": 2,
  "headless": false,
  "cookies_file": "linkedin_cookies.json"
}
```

**Parameters:**
- `url` (required): LinkedIn search results URL to scrape
- `max_scroll` (optional): Maximum number of scrolls (default: 5, range: 1-50)
- `scroll_delay` (optional): Delay between scrolls in seconds (default: 2, range: 1-10)
- `headless` (optional): Run browser in headless mode (default: false)
- `cookies_file` (optional): Path to cookies JSON file on server (default: "linkedin_cookies.json")

**Note:** Cookies are loaded from a local JSON file on the server. The `linkedin_cookies.json` file must be present in the application directory. You can specify a different file path using the `cookies_file` parameter.

**Response:**
```json
{
  "success": true,
  "posts": [
    {
      "text": "Post content here...",
      "name": "John Doe",
      "profile_link": "https://www.linkedin.com/in/johndoe",
      "job_application_link": "https://www.linkedin.com/jobs/view/123456",
      "image_links": ["https://media.licdn.com/dms/image/..."]
    }
  ],
  "count": 1,
  "message": "Successfully scraped 1 posts"
}
```

#### GET `/health`

Health check endpoint to verify the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "LinkedIn Scraper API",
  "version": "1.0.0"
}
```

### Example API Usage

**Using curl:**
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{
    "url": "https://www.linkedin.com/search/results/content/?keywords=python",
    "max_scroll": 5,
    "scroll_delay": 2,
    "headless": false
  }'
```

**Using Python requests:**
```python
import requests
import os

# Get API key from environment variable or use default
api_key = os.getenv('LINKEDIN_SCRAPER_API_KEY', 'your-secret-api-key-here')

# Make API request (cookies are loaded from server's linkedin_cookies.json file)
response = requests.post(
    'http://localhost:8000/scrape',
    headers={
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    },
    json={
        'url': 'https://www.linkedin.com/search/results/content/?keywords=python',
        'max_scroll': 5,
        'scroll_delay': 2,
        'headless': False
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Scraped {result['count']} posts")
    for post in result['posts']:
        print(f"- {post['name']}: {post['text'][:100]}...")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

**Using JavaScript/Node.js:**
```javascript
const fetch = require('node-fetch');

const apiKey = process.env.LINKEDIN_SCRAPER_API_KEY || 'your-secret-api-key-here';

fetch('http://localhost:8000/scrape', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': apiKey
  },
  body: JSON.stringify({
    url: 'https://www.linkedin.com/search/results/content/?keywords=python',
    max_scroll: 5,
    scroll_delay: 2,
    headless: false
  })
})
.then(res => res.json())
.then(data => {
  console.log(`Scraped ${data.count} posts`);
  data.posts.forEach(post => {
    console.log(`- ${post.name}: ${post.text.substring(0, 100)}...`);
  });
})
.catch(error => {
  console.error('Error:', error);
});
```

### API Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `401`: Unauthorized (missing API key)
- `403`: Forbidden (invalid API key)
- `400`: Bad Request (invalid parameters, missing required fields)
- `500`: Internal Server Error (scraping failed, unexpected errors)

**Authentication Errors:**
```json
{
  "detail": "API key is missing. Please provide X-API-Key header."
}
```

```json
{
  "detail": "Invalid API key. Access denied."
}
```

Error responses include detailed error messages:
```json
{
  "detail": {
    "error": "Scraping failed",
    "message": "Error description here",
    "details": "Full traceback (in development mode)"
  }
}
```

### Deploying the API

For production deployment, consider using:
- **Gunicorn with Uvicorn workers**: `gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker`
- **Docker**: Create a Dockerfile and deploy to container platforms
- **Cloud platforms**: Deploy to AWS, Google Cloud, Azure, or Heroku

**Important Notes:**
- **Cookies File**: The API uses a local `linkedin_cookies.json` file on the server for authentication. Make sure this file exists in the application directory before making requests.
- **Cookies File Location**: 
  - Default: `linkedin_cookies.json` in the application directory
  - Docker: Mount the file as a volume (see `docker-compose.yml`)
  - You can specify a custom path using the `cookies_file` parameter in the request
- **Updating Cookies**: When cookies expire, update the `linkedin_cookies.json` file on the server and restart the container/service.

**Note**: When deploying to a server, ensure:
1. Playwright browsers are installed: `playwright install chromium`
2. Required system dependencies are available
3. Consider running in headless mode (`headless: true`) for server environments
4. Set a strong API key via `LINKEDIN_SCRAPER_API_KEY` environment variable
5. Set up HTTPS/SSL for production use
6. Place `linkedin_cookies.json` file in the application directory or mount it as a volume

## Notes

- **Cross-Platform Compatibility**: The scraper works on Windows, macOS, and Linux. It automatically detects your OS and uses appropriate user agents.
- **macOS Compatibility**: The scraper uses Firefox by default in non-headless mode for better stability on macOS. Chromium may crash in non-headless mode on some macOS systems, so Firefox is preferred.
- **Windows Compatibility**: Works perfectly on Windows. Uses Firefox by default, but will fall back to Chromium if Firefox fails. User agents are automatically set for Windows.
- **Avoiding Detection**: Running with a visible browser window (default) helps avoid LinkedIn's bot detection. The scraper uses realistic browser settings and OS-appropriate user agents.
- **Rate Limiting**: Be respectful of LinkedIn's servers. Don't scrape too aggressively.
- **Terms of Service**: Ensure your usage complies with LinkedIn's Terms of Service.
- **Cookie Expiration**: Cookies expire after some time. You may need to refresh them periodically.
- **Dynamic Content**: LinkedIn's structure may change. The scraper may need updates if LinkedIn updates their HTML structure.

## Troubleshooting

### No posts found
- Check if you're logged in (cookies are valid)
- Verify the URL is correct
- LinkedIn may have changed their HTML structure - you may need to update selectors

### Authentication errors
- Ensure cookies are fresh and valid
- Make sure all required cookies are included (especially `li_at`)
- Try logging out and back in, then re-export cookies

### Browser not launching
- Make sure Playwright browsers are installed: `playwright install chromium`
- Check if you have necessary system dependencies

## License

This project is for educational purposes. Use responsibly and in accordance with LinkedIn's Terms of Service.

