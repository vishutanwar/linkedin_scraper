# LinkedIn Scraper - Troubleshooting Guide

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Key Components](#key-components)
4. [Common Issues & Solutions](#common-issues--solutions)
5. [Logs & Debugging](#logs--debugging)
6. [How to Troubleshoot](#how-to-troubleshoot)
7. [Information to Collect](#information-to-collect)
8. [Future Maintenance](#future-maintenance)

---

## System Overview

### What This System Does
- **Purpose**: Scrapes LinkedIn posts from search results pages
- **Input**: LinkedIn search URL (e.g., content search with keywords)
- **Output**: JSON array of posts with:
  - Post text content
  - Author name
  - Profile link
  - Job application links (if available)
  - Image links (if available)

### How It Works
1. **API Layer** (`api.py`): FastAPI REST API that receives scrape requests
2. **Worker Process** (`scrape_worker.py`): Standalone subprocess that runs the scraper
3. **Scraper** (`linkedin_scraper.py`): Core scraping logic using Playwright
4. **Browser Automation**: Uses Playwright to control Chromium browser
5. **Data Extraction**: Multiple strategies (CSS selectors → JavaScript extraction → Text pattern matching)

---

## Architecture

### File Structure
```
linkedin_scraper/
├── api.py                 # FastAPI REST API server
├── scrape_worker.py       # Subprocess worker script
├── linkedin_scraper.py    # Core scraping logic (LinkedInScraper class)
├── linkedin_cookies.json  # LinkedIn authentication cookies
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container definition
├── docker-compose.yml    # Docker Compose configuration
└── TROUBLESHOOTING.md    # This file
```

### Request Flow
```
Client Request → api.py → scrape_worker.py (subprocess) → linkedin_scraper.py → Playwright Browser → LinkedIn
                                                                                      ↓
Client Response ← api.py ← scrape_worker.py (JSON output) ← linkedin_scraper.py ← Extracted Posts
```

### Why Subprocess?
- Playwright's sync API cannot run inside asyncio event loop
- Subprocess isolation prevents browser driver communication issues
- Each request gets its own isolated browser instance

---

## Key Components

### 1. API (`api.py`)
- **Port**: 8000
- **Authentication**: API key via `X-API-Key` header (default: `shippop@122`)
- **Key Endpoints**:
  - `POST /scrape` - Main scraping endpoint
  - `GET /health` - Health check (no auth required)
- **Timeout**: 10-30 minutes (configurable, min 10min, max 30min)
- **Environment Variables**:
  - `LINKEDIN_SCRAPER_API_KEY` - API key for authentication
  - `LINKEDIN_SCRAPER_AUTH_ENABLED` - Enable/disable auth (default: true)

### 2. Scraper Worker (`scrape_worker.py`)
- **Purpose**: Runs scraping in isolated subprocess
- **Input**: JSON arguments via command line
- **Output**: JSON result to stdout (errors to stderr)
- **Why Separate**: Avoids Playwright issues with ProcessPoolExecutor

### 3. Core Scraper (`linkedin_scraper.py`)
- **Class**: `LinkedInScraper`
- **Key Methods**:
  - `scrape_posts()` - Main scraping method
  - `_extract_posts()` - Extracts posts from page
  - `_extract_single_post()` - Extracts data from single post element
- **Extraction Strategies** (in order):
  1. **CSS Selectors**: Traditional DOM selectors (fast, but breaks when LinkedIn changes structure)
  2. **JavaScript Extraction**: Runs JS in browser to find posts by content (more resilient)
  3. **Text Pattern Matching**: Fallback for finding post-like content

### 4. Browser Configuration
- **Browser**: Chromium (via Playwright)
- **Mode**: Headless (required in Docker)
- **User Agent**: Chrome on macOS/Linux/Windows (based on OS)
- **Viewport**: 1920x1080
- **Cookies**: Loaded from `linkedin_cookies.json`

---

## Common Issues & Solutions

### Issue 1: "No posts found" (0 posts returned)

**Symptoms**:
- API returns `{"success": true, "posts": [], "count": 0}`
- Logs show: "Warning: No posts found"
- Logs show: "Found 0 posts"

**Possible Causes**:
1. **LinkedIn structure changed** (most common)
   - CSS selectors no longer match
   - JavaScript extraction may still work
   
2. **Cookies expired/invalid**
   - Check logs for: "redirected to: /login" or "/checkpoint"
   - LinkedIn requires re-authentication
   
3. **Page not loading**
   - Check logs for navigation errors
   - Network issues or proxy problems
   
4. **Content not rendered yet**
   - React content needs more time to load
   - Increase wait times

**Solutions**:
1. Check Docker logs: `docker-compose logs linkedin-scraper-api`
2. Look for JavaScript extraction messages: "JavaScript extraction found X posts"
3. If JS extraction also fails, LinkedIn structure likely changed significantly
4. Check debug HTML: `/app/debug_page.html` in container
5. Verify cookies are valid (try logging into LinkedIn manually)

### Issue 2: Timeout Errors

**Symptoms**:
- "Gateway timed out" error
- "Scraping timeout" after 10 minutes

**Solutions**:
- Increase timeout in `api.py` line 330: `timeout_seconds = max(600, min(calculated_timeout, 1800))`
- Reduce `max_scroll` parameter in request
- Reduce `scroll_delay` parameter

### Issue 3: Authentication Errors

**Symptoms**:
- 401 Unauthorized
- 403 Forbidden
- "Invalid API key"

**Solutions**:
- Check API key in request header: `X-API-Key: shippop@122`
- Verify `.env` file has correct `LINKEDIN_SCRAPER_API_KEY`
- Check `api.py` loads `.env` file (should have `load_dotenv()`)

### Issue 4: Docker Issues

**Symptoms**:
- Container won't start
- Browser not found errors
- Permission errors

**Solutions**:
- Rebuild: `docker-compose build --no-cache`
- Check Playwright browsers installed: `docker-compose exec linkedin-scraper-api playwright install chromium`
- Check logs: `docker-compose logs linkedin-scraper-api`

---

## Logs & Debugging

### Where to Find Logs

#### 1. Docker Container Logs
```bash
# View all logs
docker-compose logs linkedin-scraper-api

# Follow logs in real-time
docker-compose logs -f linkedin-scraper-api

# Last 100 lines
docker-compose logs --tail=100 linkedin-scraper-api

# Filter for specific messages
docker-compose logs linkedin-scraper-api | grep -E "JavaScript|posts|error|Warning"
```

#### 2. Debug HTML File
- **Location in container**: `/app/debug_page.html`
- **When created**: When no posts found (saved for inspection)
- **How to access**:
  ```bash
  docker-compose exec linkedin-scraper-api cat /app/debug_page.html > debug_page.html
  ```
- **What to check**: 
  - Look for activity URNs: `urn:li:activity:XXXXX`
  - Check if posts are in HTML but not being extracted
  - Verify page structure

#### 3. Application Logs
- **Location**: Console output (captured in Docker logs)
- **Format**: `TIMESTAMP - LEVEL - MESSAGE`
- **Key Log Messages**:
  - `"SCRAPER: Found X posts"` - Success indicator
  - `"JavaScript extraction found X posts"` - JS extraction working
  - `"Warning: No posts found"` - Selector-based extraction failed
  - `"Found X activity URNs in page HTML"` - Posts exist in HTML

### Key Log Patterns to Monitor

#### Success Indicators
```
✅ "JavaScript extraction found X posts directly!"
✅ "Successfully extracted X posts using JavaScript!"
✅ "SCRAPER: Found X posts"
✅ "Successfully scraped X posts"
```

#### Failure Indicators
```
❌ "Warning: No posts found"
❌ "Found 0 posts"
❌ "JavaScript extraction found 0 posts"
❌ "No post elements found"
❌ "redirected to: /login" (cookie issue)
❌ "Scraping timeout"
```

#### Debugging Messages
```
🔍 "DEBUG: post_elements is empty, attempting JavaScript extraction..."
🔍 "Trying JavaScript-based post detection and extraction..."
🔍 "Found X activity URNs in page HTML"
🔍 "Page HTML saved to /app/debug_page.html"
```

---

## How to Troubleshoot

### Step-by-Step Troubleshooting Process

#### Step 1: Check API Health
```bash
curl http://localhost:8000/health
```
**Expected**: `{"status": "healthy", ...}`

#### Step 2: Test Scraping Endpoint
```bash
curl -X POST http://localhost:8000/scrape \
  -H "X-API-Key: shippop@122" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.linkedin.com/search/results/content/?keywords=%23Hiring", "max_scroll": 1, "scroll_delay": 2}'
```

#### Step 3: Check Logs
```bash
docker-compose logs --tail=100 linkedin-scraper-api | grep -E "posts|JavaScript|error|Warning"
```

#### Step 4: Verify Extraction Strategy
Look for these messages in order:
1. CSS selector attempts (should see selector counts)
2. JavaScript extraction attempt (should see "Trying JavaScript...")
3. Activity URN count (should see "Found X activity URNs")

#### Step 5: Inspect Debug HTML (if 0 posts)
```bash
# Extract debug HTML
docker-compose exec linkedin-scraper-api cat /app/debug_page.html > debug_page.html

# Check for activity URNs
grep -o 'urn:li:activity:[0-9]*' debug_page.html | head -10

# Check page structure
grep -E 'class="[^"]*feed[^"]*"|class="[^"]*update[^"]*"' debug_page.html | head -20
```

#### Step 6: Verify Cookies
```bash
# Check if cookies file exists
docker-compose exec linkedin-scraper-api ls -la /app/linkedin_cookies.json

# Check cookie count in logs
docker-compose logs linkedin-scraper-api | grep -E "cookies|li_at"
```

### Quick Diagnostic Commands

```bash
# Full diagnostic
docker-compose logs --tail=200 linkedin-scraper-api 2>&1 | \
  grep -E "posts|JavaScript|error|Warning|activity URNs|DEBUG|extraction" | \
  tail -30

# Check if container is running
docker-compose ps

# Check container resources
docker stats linkedin-scraper-api

# Test API directly
curl -X POST http://localhost:8000/scrape \
  -H "X-API-Key: shippop@122" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.linkedin.com/search/results/content/?keywords=test", "max_scroll": 1}' \
  | python3 -m json.tool
```

---

## Information to Collect

### When Reporting Issues, Collect:

#### 1. Request Details
- URL being scraped
- Request parameters (max_scroll, scroll_delay, headless)
- API key used
- Timestamp of request

#### 2. Response Details
- Full JSON response
- Count of posts returned
- Success/failure status
- Error messages

#### 3. Log Information
```bash
# Collect last 200 lines of logs
docker-compose logs --tail=200 linkedin-scraper-api > troubleshooting_logs.txt

# Collect specific error patterns
docker-compose logs linkedin-scraper-api 2>&1 | \
  grep -E "error|Error|ERROR|exception|Exception|traceback|Traceback" > errors.txt
```

#### 4. Debug HTML
```bash
# Extract debug HTML if available
docker-compose exec linkedin-scraper-api cat /app/debug_page.html > debug_page.html 2>/dev/null || echo "No debug file"
```

#### 5. System Information
- Docker version: `docker --version`
- Docker Compose version: `docker-compose --version`
- Container status: `docker-compose ps`
- Container logs: `docker-compose logs --tail=50 linkedin-scraper-api`

#### 6. Page Structure Analysis
```bash
# Check what selectors are being tried
docker-compose logs linkedin-scraper-api | grep -E "Found.*elements matching|selector"

# Check activity URNs in page
docker-compose logs linkedin-scraper-api | grep "activity URNs"
```

### Key Metrics to Track
- **Success Rate**: Posts found / Requests made
- **Extraction Method**: CSS vs JavaScript (log which one worked)
- **Average Posts per Request**: Track if it decreases over time
- **Timeout Frequency**: How often requests timeout
- **Cookie Expiry**: When cookies need refreshing

---

## Future Maintenance

### Regular Checks

#### Weekly
- [ ] Test scraping with a known-good URL
- [ ] Check logs for new error patterns
- [ ] Verify cookies are still valid
- [ ] Monitor success rate

#### Monthly
- [ ] Update Playwright if new version available
- [ ] Review and update CSS selectors if needed
- [ ] Check LinkedIn for UI changes
- [ ] Update user agent strings if needed

#### When LinkedIn Changes Structure

1. **Symptoms**:
   - Success rate drops to 0%
   - JavaScript extraction also fails
   - Debug HTML shows different structure

2. **Actions**:
   - Inspect debug HTML for new class names
   - Update CSS selectors in `linkedin_scraper.py` (line ~894)
   - Update JavaScript extraction logic (line ~1100)
   - Test with small `max_scroll` first
   - Update this troubleshooting guide with new patterns

### Code Locations for Common Fixes

#### Update CSS Selectors
- **File**: `linkedin_scraper.py`
- **Location**: Line ~894 (`post_selectors` list)
- **What to do**: Add new selectors based on debug HTML inspection

#### Update JavaScript Extraction
- **File**: `linkedin_scraper.py`
- **Location**: Line ~1100 (JavaScript `page.evaluate()` block)
- **What to do**: Modify element detection logic

#### Adjust Wait Times
- **File**: `linkedin_scraper.py`
- **Location**: Line ~447 (wait for React content)
- **What to do**: Increase `time.sleep()` values if content loads slowly

#### Update Timeout
- **File**: `api.py`
- **Location**: Line ~330
- **What to do**: Adjust `timeout_seconds` calculation

#### Update API Key
- **File**: `.env`
- **Location**: `LINKEDIN_SCRAPER_API_KEY=your-key`
- **What to do**: Change value and restart container

### Testing Checklist

After making changes:
- [ ] Test with simple URL first
- [ ] Verify posts are returned
- [ ] Check logs for errors
- [ ] Test with original problematic URL
- [ ] Verify all post fields are populated
- [ ] Check for duplicates
- [ ] Test timeout handling

---

## Known Limitations

1. **LinkedIn Structure Changes**: CSS selectors break when LinkedIn updates UI
2. **Cookie Expiry**: Cookies need periodic refresh (typically every few weeks)
3. **Rate Limiting**: Too many requests may trigger LinkedIn's rate limiting
4. **Text Quality**: Some navigation/UI text may appear in post content
5. **Duplicates**: Some posts may appear multiple times (deduplication can be added)

---

## Quick Reference

### Restart Services
```bash
docker-compose restart linkedin-scraper-api
```

### Rebuild After Code Changes
```bash
docker-compose build --no-cache linkedin-scraper-api
docker-compose up -d
```

### View Real-time Logs
```bash
docker-compose logs -f linkedin-scraper-api
```

### Test API
```bash
curl -X POST http://localhost:8000/scrape \
  -H "X-API-Key: shippop@122" \
  -H "Content-Type: application/json" \
  -d '{"url": "YOUR_LINKEDIN_URL", "max_scroll": 3, "scroll_delay": 2}'
```

### Check Container Status
```bash
docker-compose ps
docker-compose logs --tail=20 linkedin-scraper-api
```

---

## Notes for AI Assistants

When troubleshooting this scraper:

1. **Always check logs first** - They contain detailed information about what's happening
2. **Look for JavaScript extraction messages** - This is the fallback that often works when CSS fails
3. **Check debug HTML** - Contains the actual page structure when extraction fails
4. **Activity URNs** - If these exist in HTML but posts aren't extracted, it's a selector/extraction issue
5. **Cookie validation** - Check for login/checkpoint redirects in logs
6. **Multiple extraction strategies** - The code tries CSS first, then JavaScript, then text patterns
7. **Subprocess isolation** - Worker runs in separate process to avoid Playwright/async issues

### Key Code Sections to Modify
- **Line ~894**: CSS selectors for posts
- **Line ~1100**: JavaScript extraction logic
- **Line ~447**: Wait times for React content
- **Line ~330**: Timeout calculation
- **Line ~1195**: JavaScript extraction (runs when CSS fails)

### Common Fix Patterns
- **0 posts but activity URNs exist**: Update selectors or JavaScript extraction
- **Timeout errors**: Increase timeout or reduce max_scroll
- **Login redirects**: Refresh cookies
- **JavaScript extraction fails**: Update element detection criteria

---

**Last Updated**: 2026-01-31
**Version**: 1.0
**Maintainer**: Add your name/contact here
