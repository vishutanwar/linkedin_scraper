# Deployment Guide

This guide will help you deploy the LinkedIn Scraper API on your server so you can access it from anywhere.

## Prerequisites

- A Linux server (Ubuntu 20.04+ recommended)
- Root or sudo access
- Domain name (optional but recommended for HTTPS)
- Basic knowledge of Linux commands

## Option 1: Docker Deployment (Recommended)

Docker is the easiest way to deploy the API. It handles all dependencies automatically.

### Step 1: Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (optional)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Step 2: Clone/Upload Your Project

```bash
# If using git
git clone <your-repo-url> /opt/linkedin-scraper
cd /opt/linkedin-scraper

# Or upload files via SCP/SFTP to /opt/linkedin-scraper
```

### Step 3: Configure Environment Variables
### Setup from here----
```bash
cd /opt/linkedin-scraper

# Create .env file
cp .env.example .env
nano .env  # Edit with your API key
```

Set your API key:
```
LINKEDIN_SCRAPER_API_KEY=your-strong-secret-api-key-here
LINKEDIN_SCRAPER_AUTH_ENABLED=true
```

### Step 4: Build and Run

```bash
# Build and start the container
docker-compose up -d

# Check logs
docker-compose logs -f

# Check status
docker-compose ps
```

The API will be running on `http://your-server-ip:8000`

### Step 5: Set Up Nginx Reverse Proxy (Optional but Recommended)

```bash
# Install Nginx
sudo apt install nginx -y

# Copy nginx config
sudo cp nginx.conf.example /etc/nginx/sites-available/linkedin-scraper-api

# Edit the config
sudo nano /etc/nginx/sites-available/linkedin-scraper-api
# Update: server_name your-domain.com;

# Enable the site
sudo ln -s /etc/nginx/sites-available/linkedin-scraper-api /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

### Step 6: Set Up SSL with Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Certbot will automatically configure Nginx for HTTPS
```

### Step 7: Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# If not using Nginx, allow port 8000
# sudo ufw allow 8000/tcp

# Enable firewall
sudo ufw enable
```

## Option 2: Systemd Service (Native Python)

If you prefer not to use Docker, you can run it as a systemd service.

### Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv -y

# Install Playwright system dependencies
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

### Step 2: Set Up Application

```bash
# Create directory
sudo mkdir -p /opt/linkedin-scraper
sudo chown $USER:$USER /opt/linkedin-scraper

# Upload your files to /opt/linkedin-scraper
cd /opt/linkedin-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
playwright install-deps chromium
```

### Step 3: Configure Environment Variables

```bash
# Create .env file
cp .env.example .env
nano .env  # Set your API key
```

### Step 4: Set Up Systemd Service

```bash
# Copy service file
sudo cp linkedin-scraper-api.service /etc/systemd/system/

# Edit the service file
sudo nano /etc/systemd/system/linkedin-scraper-api.service
# Update:
# - WorkingDirectory path
# - User/Group (or create a dedicated user)
# - Environment variables (API key)

# Create dedicated user (recommended)
sudo useradd -r -s /bin/false -d /opt/linkedin-scraper linkedin-scraper
sudo chown -R linkedin-scraper:linkedin-scraper /opt/linkedin-scraper

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable linkedin-scraper-api
sudo systemctl start linkedin-scraper-api

# Check status
sudo systemctl status linkedin-scraper-api

# View logs
sudo journalctl -u linkedin-scraper-api -f
```

### Step 5: Set Up Nginx (Same as Docker Option)

Follow Step 5 and 6 from the Docker deployment section.

## Testing Your Deployment

### Test Locally on Server

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test scrape endpoint (replace with your API key)
curl -X POST "http://localhost:8000/scrape" \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.linkedin.com/search/results/content/?keywords=test",
    "cookies": [...],
    "max_scroll": 2,
    "headless": true
  }'
```

### Test from Your Local Machine

```bash
# Replace with your server IP or domain
curl http://your-server-ip:8000/health

# Or with domain
curl https://your-domain.com/health
```

## Maintenance

### View Logs

**Docker:**
```bash
docker-compose logs -f linkedin-scraper-api
```

**Systemd:**
```bash
sudo journalctl -u linkedin-scraper-api -f
```

### Restart Service

**Docker:**
```bash
docker-compose restart
```

**Systemd:**
```bash
sudo systemctl restart linkedin-scraper-api
```

### Update Application

**Docker:**
```bash
cd /opt/linkedin-scraper
git pull  # If using git
docker-compose build
docker-compose up -d
```

**Systemd:**
```bash
cd /opt/linkedin-scraper
git pull  # If using git
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart linkedin-scraper-api
```

## Security Best Practices

1. **Change Default API Key**: Always use a strong, unique API key
2. **Use HTTPS**: Set up SSL/TLS certificate (Let's Encrypt is free)
3. **Firewall**: Only expose necessary ports (80, 443)
4. **Keep Updated**: Regularly update system packages and dependencies
5. **Monitor Logs**: Check logs regularly for suspicious activity
6. **Rate Limiting**: Consider adding rate limiting (can be done in Nginx)

## Troubleshooting

### API Not Responding

```bash
# Check if service is running
docker-compose ps  # or
sudo systemctl status linkedin-scraper-api

# Check logs
docker-compose logs  # or
sudo journalctl -u linkedin-scraper-api -n 50
```

### Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process or change port in docker-compose.yml/service file
```

### Playwright Browser Issues

```bash
# Reinstall browsers
docker-compose exec linkedin-scraper-api playwright install chromium
# or
cd /opt/linkedin-scraper && source venv/bin/activate && playwright install chromium
```

### Permission Issues

```bash
# Fix permissions
sudo chown -R $USER:$USER /opt/linkedin-scraper
# or for systemd user
sudo chown -R linkedin-scraper:linkedin-scraper /opt/linkedin-scraper
```

## Using the API

Once deployed, you can use the API from anywhere:

```python
import requests

response = requests.post(
    'https://your-domain.com/scrape',  # or http://your-server-ip:8000/scrape
    headers={
        'X-API-Key': 'your-secret-api-key-here',
        'Content-Type': 'application/json'
    },
    json={
        'url': 'https://www.linkedin.com/search/results/content/?keywords=python',
        'cookies': [...],  # Your LinkedIn cookies
        'max_scroll': 5,
        'scroll_delay': 2,
        'headless': True
    }
)

print(response.json())
```

## Support

If you encounter issues:
1. Check the logs (see Maintenance section)
2. Verify environment variables are set correctly
3. Ensure firewall allows necessary ports
4. Check Nginx configuration if using reverse proxy

