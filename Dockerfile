FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright and curl for healthcheck
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    curl \
    fonts-unifont \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security (before installing browsers)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Install Playwright browsers as appuser so they're in the correct location
# Note: We've already installed all system dependencies above, so we don't need install-deps
USER appuser
RUN playwright install chromium

# Copy application code (copy all Python files)
# Switch back to root temporarily to copy files
USER root
COPY *.py ./
RUN chmod +x scrape_worker.py
RUN chown -R appuser:appuser /app

# Note: Cookies file should be mounted as a volume or copied separately
# The default location is /app/linkedin_cookies.json

# Switch back to appuser for runtime
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with increased timeouts for long-running scraping requests
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "600", "--timeout-graceful-shutdown", "600"]

