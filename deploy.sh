#!/bin/bash
# Quick deployment script for LinkedIn Scraper API

set -e

echo "🚀 LinkedIn Scraper API Deployment Script"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  Please don't run as root. Use sudo when needed."
   exit 1
fi

# Check for Docker
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✅ Docker and Docker Compose found"
    USE_DOCKER=true
else
    echo "⚠️  Docker not found. Will use systemd service instead."
    USE_DOCKER=false
fi

# Get API key
if [ -z "$LINKEDIN_SCRAPER_API_KEY" ]; then
    echo ""
    read -sp "Enter your API key (or press Enter to use default): " API_KEY
    echo ""
    if [ -z "$API_KEY" ]; then
        API_KEY="your-secret-api-key-change-this"
        echo "⚠️  Using default API key. Please change it in production!"
    fi
    export LINKEDIN_SCRAPER_API_KEY="$API_KEY"
else
    echo "✅ API key found in environment"
fi

if [ "$USE_DOCKER" = true ]; then
    echo ""
    echo "🐳 Deploying with Docker..."
    echo ""
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        echo "Creating .env file..."
        cat > .env << EOF
LINKEDIN_SCRAPER_API_KEY=${API_KEY}
LINKEDIN_SCRAPER_AUTH_ENABLED=true
EOF
    fi
    
    # Build and start
    echo "Building Docker image..."
    docker-compose build
    
    echo "Starting containers..."
    docker-compose up -d
    
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "Check status: docker-compose ps"
    echo "View logs: docker-compose logs -f"
    echo "Stop: docker-compose down"
    
else
    echo ""
    echo "📦 Deploying with systemd service..."
    echo ""
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 not found. Please install Python 3.9+ first."
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate and install dependencies
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium
    playwright install-deps chromium
    
    # Set up systemd service
    echo "Setting up systemd service..."
    sudo cp linkedin-scraper-api.service /etc/systemd/system/
    
    # Update service file with current directory and API key
    sudo sed -i "s|WorkingDirectory=/opt/linkedin-scraper|WorkingDirectory=$(pwd)|g" /etc/systemd/system/linkedin-scraper-api.service
    sudo sed -i "s|Environment=\"LINKEDIN_SCRAPER_API_KEY=.*\"|Environment=\"LINKEDIN_SCRAPER_API_KEY=${API_KEY}\"|g" /etc/systemd/system/linkedin-scraper-api.service
    
    # Reload and start
    sudo systemctl daemon-reload
    sudo systemctl enable linkedin-scraper-api
    sudo systemctl start linkedin-scraper-api
    
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "Check status: sudo systemctl status linkedin-scraper-api"
    echo "View logs: sudo journalctl -u linkedin-scraper-api -f"
    echo "Stop: sudo systemctl stop linkedin-scraper-api"
fi

echo ""
echo "🌐 API should be running on http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""
echo "⚠️  Don't forget to:"
echo "   1. Set up firewall (ufw allow 8000/tcp or use Nginx)"
echo "   2. Configure Nginx reverse proxy (see nginx.conf.example)"
echo "   3. Set up SSL/HTTPS (see DEPLOYMENT.md)"
echo ""

