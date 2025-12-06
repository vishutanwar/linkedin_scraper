# Quick Deployment Guide

## Minimal Steps to Deploy

### 1. On Your Server

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in
```

### 2. Transfer Project Files

```bash
# Option 1: Git
git clone <your-repo-url>
cd linkedin_scraper

# Option 2: SCP (from your local machine)
scp -r linkedin_scraper/ user@server:~/linkedin_scraper
```

### 3. Set Up Cookies

```bash
cd ~/linkedin_scraper
nano linkedin_cookies.json
# Paste your cookies JSON array here
```

### 4. Configure Environment

```bash
cp env.example .env
nano .env
# Set: LINKEDIN_SCRAPER_API_KEY=your-random-key-here
```

### 5. Deploy

```bash
docker-compose build
docker-compose up -d
docker-compose logs -f
```

### 6. Test

```bash
curl http://localhost:8000/health
```

## That's It!

For detailed instructions, see `DEPLOY.md`.

