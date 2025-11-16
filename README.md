# LinkedIn Post Scraper

A Python tool to scrape LinkedIn posts from search results pages. Extracts post text, job application links, profile links, images, and poster names.

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

**On Windows:**
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
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

**Note:** Remember to activate the virtual environment (`source venv/bin/activate` on macOS/Linux) each time you want to use the scraper.

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

## Notes

- **macOS Compatibility**: The scraper uses Firefox by default in non-headless mode for better stability on macOS. Chromium may crash in non-headless mode on some macOS systems, so Firefox is preferred.
- **Avoiding Detection**: Running with a visible browser window (default) helps avoid LinkedIn's bot detection. The scraper uses realistic browser settings and user agents.
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

