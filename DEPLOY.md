# Deployment Guide

This guide will help you deploy the LinkedIn Scraper API to any server.

## Prerequisites

- Server with Ubuntu 20.04+ (or similar Linux distribution)
- Docker and Docker Compose installed
- At least 2GB RAM and 10GB disk space
- Root or sudo access

## Step 1: Prepare Your Server

### 1.1 Install Docker and Docker Compose

```bash
# Update package index
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes to take effect
```

### 1.2 Verify Installation

```bash
docker --version
docker-compose --version
```

## Step 2: Transfer Files to Server

### Option A: Using Git (Recommended)

```bash
# On your local machine, initialize git if not already done
cd /path/to/linkedin_scraper
git init
git add .
git commit -m "Initial commit"

# Create a repository on GitHub/GitLab and push
git remote add origin <your-repo-url>
git push -u origin main

# On your server
cd ~
git clone <your-repo-url>
cd linkedin_scraper
```

### Option B: Using SCP

```bash
# On your local machine
scp -r /path/to/linkedin_scraper user@your-server-ip:~/
```

### Option C: Using rsync

```bash
# On your local machine
rsync -avz --exclude 'venv' --exclude 'logs' --exclude '__pycache__' \
  /path/to/linkedin_scraper/ user@your-server-ip:~/linkedin_scraper/
```

## Step 3: Set Up Cookies File

**IMPORTANT:** You need to provide your LinkedIn cookies file on the server.

```bash
# On your server, create the cookies file
cd ~/linkedin_scraper
nano linkedin_cookies.json
# Paste your cookies JSON here, then save (Ctrl+X, Y, Enter)
```

The cookies file should be a JSON array like:
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

## Step 4: Configure Environment Variables

```bash
# Copy the example env file
cp env.example .env

# Edit the environment file
nano .env
```

Set your API key:
```
LINKEDIN_SCRAPER_API_KEY=your-secret-api-key-here
LINKEDIN_SCRAPER_AUTH_ENABLED=true
```

**Security Note:** Use a strong, random API key. Generate one with:
```bash
openssl rand -hex 32
```

## Step 5: Build and Start the Container

```bash
# Build the Docker image
docker-compose build

# Start the service
docker-compose up -d

# Check if it's running
docker-compose ps

# View logs
docker-compose logs -f
```

## Step 6: Verify Deployment

### 6.1 Check Health Endpoint

```bash
# From the server
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","service":"LinkedIn Scraper API","version":"1.0.0","authentication":"enabled"}
```

### 6.2 Test the API

```bash
# Test scraping endpoint (replace YOUR_API_KEY with your actual key)
curl -X POST "http://localhost:8000/scrape" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.linkedin.com/search/results/content/?keywords=n8n",
    "max_scroll": 2,
    "scroll_delay": 2
  }'
```

## Step 7: Set Up Reverse Proxy (Optional but Recommended)

### 7.1 Install Nginx

```bash
sudo apt-get update
sudo apt-get install nginx
```

### 7.2 Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/linkedin-scraper
```

Add this configuration:

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

### 7.3 Enable the Site

```bash
sudo ln -s /etc/nginx/sites-available/linkedin-scraper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7.4 Set Up SSL with Let's Encrypt (Recommended)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Step 8: Set Up Firewall

```bash
# Allow SSH (important!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

## Step 9: Auto-Start on Boot

Docker Compose services automatically restart if the container stops, but to ensure it starts on server boot:

```bash
# Create a systemd service
sudo nano /etc/systemd/system/linkedin-scraper.service
```

Add this content:

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

Replace `YOUR_USERNAME` with your actual username.

```bash
# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable linkedin-scraper.service
sudo systemctl start linkedin-scraper.service
```

## Step 10: Monitoring and Maintenance

### View Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Logs for specific service
docker-compose logs linkedin-scraper-api
```

### Restart Service

```bash
docker-compose restart
```

### Update the Service

```bash
# Pull latest code (if using git)
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Check Resource Usage

```bash
docker stats linkedin-scraper-api
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Check if port is already in use
sudo netstat -tulpn | grep 8000

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

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

If you get out of memory errors, increase Docker's memory limit or add swap:

```bash
# Add 2GB swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
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

