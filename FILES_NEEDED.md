# Required Files for Deployment

## Essential Files (Must Have)

### Core Application Files
- `api.py` - FastAPI application
- `linkedin_scraper.py` - Scraper logic
- `scrape_worker.py` - Worker subprocess script
- `requirements.txt` - Python dependencies

### Docker Files
- `Dockerfile` - Docker image definition
- `docker-compose.yml` - Docker Compose configuration
- `.dockerignore` - Files to exclude from Docker build

### Configuration Files
- `env.example` - Environment variables template
- `.gitignore` - Git ignore rules

### Documentation (Optional but Recommended)
- `README.md` - Project documentation
- `DEPLOY.md` - Detailed deployment guide
- `DEPLOYMENT_QUICKSTART.md` - Quick deployment steps
- `TESTING.md` - Testing instructions

### Scripts (Optional)
- `deploy.sh` - Deployment automation script

## Files to Create on Server

### Required
- `linkedin_cookies.json` - Your LinkedIn cookies (create on server, don't commit)
- `.env` - Environment variables (copy from `env.example`)

### Optional
- `logs/` - Directory for logs (created automatically)

## Files Removed (Not Needed)

The following files have been removed as they're not needed for deployment:
- `debug_page.html` - Debug file
- `example_usage.py` - Example script
- `extract_cookies.py` - Utility script
- `test_api.sh` - Test script
- `linkedin-scraper-api.service` - Systemd service (can be created on server if needed)
- `nginx.conf.example` - Nginx example (can be created on server if needed)
- `venv/` - Virtual environment (not needed in Docker)
- `logs/` - Log directory (created at runtime)

## Project Structure

```
linkedin_scraper/
├── api.py                    # FastAPI application
├── linkedin_scraper.py       # Scraper logic
├── scrape_worker.py          # Worker subprocess
├── requirements.txt           # Dependencies
├── Dockerfile                # Docker image
├── docker-compose.yml        # Docker Compose config
├── .dockerignore            # Docker ignore rules
├── .gitignore               # Git ignore rules
├── env.example               # Environment template
├── README.md                 # Documentation
├── DEPLOY.md                 # Deployment guide
├── DEPLOYMENT_QUICKSTART.md  # Quick start
├── TESTING.md                # Testing guide
└── deploy.sh                 # Deployment script (optional)
```

## Minimum Files for Deployment

If you want to deploy with minimal files, you only need:

1. `api.py`
2. `linkedin_scraper.py`
3. `scrape_worker.py`
4. `requirements.txt`
5. `Dockerfile`
6. `docker-compose.yml`
7. `.dockerignore`

Plus create on server:
- `linkedin_cookies.json`
- `.env`

