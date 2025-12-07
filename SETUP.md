# Setup & Deployment Guide

Complete guide for setting up and deploying the LinkedIn Scraper API.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Docker Deployment](#docker-deployment)
- [Server Deployment](#server-deployment)
- [Proxy Configuration](#proxy-configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Docker** and **Docker Compose** (for containerized deployment)
- **Python 3.9+** (for local development)
- **LinkedIn Account** with valid cookies
- **Server** with Ubuntu 20.04+ (for production deployment)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd linkedin_scraper
```

### 2. Set Up Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Configure Cookies

Create `linkedin_cookies.json` in the project root with your LinkedIn cookies:

```json
[
  {
    "name": "li_at",
    "value": "your-cookie-value",
    "domain": ".linkedin.com",
    "path": "/",
    "expires": -1,
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
  }
]
```

**How to get cookies:**
1. Log in to LinkedIn in your browser
2. Use a browser extension like "Cookie Editor" to export cookies as JSON
3. Save the exported JSON as `linkedin_cookies.json`

### 4. Run Locally

```bash
# Set API key (optional)
export LINKEDIN_SCRAPER_API_KEY="your-secret-key"

# Start the API
uvicorn api:app --host 0.0.0.0 --port 8000
```

Access the API at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Docker Deployment

### Quick Start

```bash
# 1. Ensure linkedin_cookies.json exists
ls linkedin_cookies.json

# 2. Build and start
docker-compose build
docker-compose up -d

# 3. Check status
docker-compose ps
docker-compose logs -f
```

### Configuration

1. **Set API Key** (create `.env` file):
```bash
cp env.example .env
nano .env
```

Add:
```
LINKEDIN_SCRAPER_API_KEY=your-strong-random-api-key-here
LINKEDIN_SCRAPER_AUTH_ENABLED=true
```

2. **Mount Cookies File**: The `docker-compose.yml` already mounts `linkedin_cookies.json`. Ensure it exists in the project root.

### Docker Commands

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Rebuild after code changes
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Server Deployment

### Step 1: Install Docker on Server

```bash
# Update system
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes
```

### Step 2: Transfer Project to Server

**Option A: Using Git (Recommended)**
```bash
# On server
cd ~
git clone <your-repo-url>
cd linkedin_scraper
```

**Option B: Using SCP**
```bash
# From local machine
scp -r linkedin_scraper/ user@server-ip:~/linkedin_scraper
```

### Step 3: Set Up Cookies File

```bash
# On server
cd ~/linkedin_scraper
nano linkedin_cookies.json
# Paste your cookies JSON array
```

### Step 4: Configure Environment

```bash
# Copy example env file
cp env.example .env

# Edit and set your API key
nano .env
```

Generate a strong API key:
```bash
openssl rand -hex 32
```

### Step 5: Deploy

```bash
# Build and start
docker-compose build
docker-compose up -d

# Verify it's running
docker-compose ps
curl http://localhost:8000/health
```

### Step 6: Set Up Reverse Proxy (Optional but Recommended)

**Install Nginx:**
```bash
sudo apt-get install nginx
```

**Create Nginx Config:**
```bash
sudo nano /etc/nginx/sites-available/linkedin-scraper
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or IP

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeouts for long-running requests
        proxy_read_timeout 1800s;
        proxy_connect_timeout 600s;
    }
}
```

**Enable Site:**
```bash
sudo ln -s /etc/nginx/sites-available/linkedin-scraper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Set Up SSL (Recommended):**
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Step 7: Configure Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### Step 8: Auto-Start on Boot

Create systemd service:
```bash
sudo nano /etc/systemd/system/linkedin-scraper.service
```

Add:
```ini
[Unit]
Description=LinkedIn Scraper API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/YOUR_USERNAME/linkedin_scraper
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable linkedin-scraper.service
sudo systemctl start linkedin-scraper.service
```

## Proxy Configuration

The API supports proxy configuration to avoid IP blocking and improve reliability.

### Using Proxy in API Request

```json
{
  "url": "https://www.linkedin.com/search/results/content/?keywords=n8n",
  "max_scroll": 5,
  "scroll_delay": 2,
  "proxy": {
    "server": "http://proxy.example.com:8080"
  }
}
```

### With Authentication

```json
{
  "proxy": {
    "server": "http://proxy.example.com:8080",
    "username": "proxy-user",
    "password": "proxy-pass"
  }
}
```

### Example: cURL with Proxy

```bash
curl -X POST "http://your-server:8000/scrape" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.linkedin.com/search/results/content/?keywords=n8n",
    "max_scroll": 5,
    "scroll_delay": 2,
    "proxy": {
      "server": "http://your-proxy-server:port"
    }
  }'
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### No Posts Found

1. **Check logs for debugging info:**
   ```bash
   docker-compose logs -f | grep SCRAPER
   ```

2. **Verify cookies are valid:**
   - Check if cookies file exists: `docker exec linkedin-scraper-api ls -la /app/linkedin_cookies.json`
   - Update cookies if expired

3. **Check if LinkedIn is blocking:**
   - Look for "login" or "challenge" in page title in logs
   - Consider using a proxy

4. **Verify URL is correct:**
   - Ensure it's a LinkedIn search results URL
   - Check if URL is accessible

### Playwright Issues

```bash
# Check if browsers are installed
docker exec linkedin-scraper-api ls -la ~/.cache/ms-playwright/

# Reinstall browsers
docker exec linkedin-scraper-api playwright install chromium
```

### Permission Issues

```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
# Log out and back in
```

### Out of Memory

Add swap space:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Proxy Not Working

1. Test proxy separately:
   ```bash
   curl -x http://proxy:port https://www.linkedin.com
   ```

2. Check proxy format: `http://host:port` or `https://host:port`

3. Verify proxy credentials if authentication is required

4. Check firewall rules on server

## Monitoring

### View Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Filter for errors
docker-compose logs | grep ERROR
```

### Check Resource Usage

```bash
docker stats linkedin-scraper-api
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Security Best Practices

1. **Use Strong API Keys**: Generate random, long API keys
2. **Enable Firewall**: Only open necessary ports
3. **Use HTTPS**: Set up SSL/TLS certificates
4. **Keep Updated**: Regularly update Docker images and system packages
5. **Monitor Logs**: Check logs regularly for suspicious activity
6. **Backup Cookies**: Keep a backup of your cookies file (securely)
7. **Limit Access**: Use firewall rules to limit API access to trusted IPs if possible

## Quick Reference

```bash
# Start service
docker-compose up -d

# Stop service
docker-compose down

# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Rebuild after code changes
docker-compose build && docker-compose up -d

# Check status
docker-compose ps

# Access container shell
docker exec -it linkedin-scraper-api /bin/bash
```

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify all files are present (especially `linkedin_cookies.json`)
3. Ensure Docker has enough resources (memory, disk space)
4. Check network connectivity and firewall rules

