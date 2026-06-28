#!/usr/bin/env python3
"""
LinkedIn Scraper API
FastAPI REST API service for scraping LinkedIn posts.
"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import List, Dict, Optional
import traceback
import asyncio
import os
import sys
import logging
import json
import subprocess
from dotenv import load_dotenv
from linkedin_scraper import LinkedInScraper

# Load environment variables from .env file
load_dotenv()

# Note: We use subprocess.Popen instead of ProcessPoolExecutor
# to avoid Playwright's driver process communication issues

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Key configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Get API key from environment variable or use default
API_KEY = os.getenv("LINKEDIN_SCRAPER_API_KEY", "your-secret-api-key-change-this")

# Disable authentication if API_KEY is set to empty string (for development)
AUTH_ENABLED = os.getenv("LINKEDIN_SCRAPER_AUTH_ENABLED", "true").lower() == "true"

app = FastAPI(
    title="LinkedIn Scraper API",
    description="API service for scraping LinkedIn posts from search results. Requires API key authentication.",
    version="1.0.0"
)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    """
    Verify the API key from the request header.
    
    Args:
        api_key: API key from the X-API-Key header
        
    Returns:
        bool: True if API key is valid
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not AUTH_ENABLED:
        return True
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is missing. Please provide X-API-Key header."
        )
    
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key. Access denied."
        )
    
    return True


class CookieModel(BaseModel):
    """Cookie model for validation."""
    name: str
    value: str
    domain: str
    path: str = "/"
    expires: Optional[int] = None
    httpOnly: Optional[bool] = None
    secure: Optional[bool] = None
    sameSite: Optional[str] = None


class ProxyConfig(BaseModel):
    """Proxy configuration model."""
    server: str = Field(..., description="Proxy server URL (e.g., 'http://proxy.example.com:8080')")
    username: Optional[str] = Field(None, description="Proxy username (optional)")
    password: Optional[str] = Field(None, description="Proxy password (optional)")


class ScrapeRequest(BaseModel):
    """Request model for scraping LinkedIn posts."""
    url: HttpUrl = Field(..., description="LinkedIn search results URL to scrape")
    max_scroll: int = Field(default=5, ge=1, le=50, description="Maximum number of scrolls to load more posts")
    scroll_delay: int = Field(default=2, ge=1, le=10, description="Delay between scrolls in seconds")
    headless: bool = Field(default=False, description="Run browser in headless mode")
    cookies_file: str = Field(default="linkedin_cookies.json", description="Path to cookies JSON file (relative to app directory)")
    proxy: Optional[ProxyConfig] = Field(
        None,
        description="Optional proxy configuration for the browser"
    )

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Ensure URL is a LinkedIn URL."""
        url_str = str(v)
        if 'linkedin.com' not in url_str.lower():
            raise ValueError("URL must be a LinkedIn URL")
        return v


class CommentData(BaseModel):
    """Comment data model."""
    commenter_name: str
    commenter_profile_link: str
    comment_text: str


class PostData(BaseModel):
    """Post data model."""
    text: str
    name: str
    profile_link: str
    job_application_link: str
    post_link: str = ""
    image_links: List[str]
    comments: List[CommentData] = []


class ScrapeResponse(BaseModel):
    """Response model for scraping results."""
    success: bool
    posts: List[PostData]
    count: int
    message: str


class ScrapeCommentsRequest(BaseModel):
    """Request model for scraping comments from a specific post URL."""
    post_url: HttpUrl = Field(..., description="LinkedIn post URL to scrape comments from")
    max_comments: int = Field(default=50, ge=1, le=500, description="Maximum number of comments to extract")
    headless: bool = Field(default=False, description="Run browser in headless mode")
    cookies_file: str = Field(default="linkedin_cookies.json", description="Path to cookies JSON file (relative to app directory)")

    @field_validator('post_url')
    @classmethod
    def validate_post_url(cls, v):
        """Ensure URL is a LinkedIn URL."""
        url_str = str(v)
        if 'linkedin.com' not in url_str.lower():
            raise ValueError("URL must be a LinkedIn URL")
        return v


class ScrapeCommentsResponse(BaseModel):
    """Response model for scraping comments."""
    success: bool
    comments: List[CommentData]
    count: int
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    message: str
    details: Optional[str] = None


async def run_scraping_in_subprocess(action: str, args_dict: dict, timeout_seconds: float):
    """
    Run scraping using subprocess.Popen instead of ProcessPoolExecutor.
    This avoids Playwright's issues with ProcessPoolExecutor.
    """
    # Prepare arguments as JSON
    payload = {
        'action': action,
        **args_dict
    }
    args_json = json.dumps(payload)
    
    # Get path to worker script
    script_dir = os.path.dirname(__file__)
    worker_script = os.path.join(script_dir, 'scrape_worker.py')
    
    # Set environment variables for the subprocess
    env = os.environ.copy()
    env['PLAYWRIGHT_BROWSERS_PATH'] = os.path.expanduser('~/.cache/ms-playwright')
    env['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '0'
    env['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = '1'
    
    # Run the worker script as a subprocess
    logger.info(f"Starting subprocess worker: {worker_script} for action: {action}")
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        worker_script,
        args_json,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
        cwd=script_dir
    )
    
    # Read output with timeout
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=float(timeout_seconds)
        )
        
        # Decode output
        stdout_text = stdout.decode('utf-8') if stdout else ""
        stderr_text = stderr.decode('utf-8') if stderr else ""
        
        # Log stderr output for debugging (contains all scraper debug messages)
        if stderr_text:
            logger.info(f"Worker process output (stderr):\n{stderr_text[-2000:]}")  # Last 2000 chars to avoid too much logging
        
        if process.returncode != 0:
            error_output = stderr_text or stdout_text or "Unknown error"
            logger.error(f"Worker subprocess failed with code {process.returncode}")
            logger.error(f"STDERR: {stderr_text}")
            logger.error(f"STDOUT: {stdout_text}")
            raise Exception(f"Scraping failed: {error_output}")
        
        # Check if stdout is empty
        if not stdout_text or not stdout_text.strip():
            error_msg = f"No output from worker. STDERR: {stderr_text}"
            logger.error(error_msg)
            raise Exception(f"Scraping failed: {error_msg}")
        
        # Parse JSON result
        try:
            stdout_text = stdout_text.strip()
            json_start = stdout_text.find('{')
            if json_start >= 0:
                stdout_text = stdout_text[json_start:]
            result = json.loads(stdout_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from worker output")
            logger.error(f"STDOUT (first 500 chars): {stdout_text[:500]}")
            logger.error(f"STDERR (first 500 chars): {stderr_text[:500]}")
            raise Exception(f"Failed to parse worker output as JSON: {str(e)}. STDOUT: {stdout_text[:200]}")
        
        if not result.get('success', False):
            raise Exception(result.get('error', 'Unknown error'))
        
        return result
        
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise asyncio.TimeoutError("Scraping subprocess timed out")
        
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise asyncio.TimeoutError("Scraping subprocess timed out")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    This endpoint does not require authentication.
    """
    return {
        "status": "healthy",
        "service": "LinkedIn Scraper API",
        "version": "1.0.0",
        "authentication": "enabled" if AUTH_ENABLED else "disabled"
    }


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_linkedin_posts(
    request: ScrapeRequest,
    api_key_verified: bool = Depends(verify_api_key)
):
    """
    Scrape LinkedIn posts from the provided URL.
    
    Note: Cookies are loaded from a local JSON file on the server (default: linkedin_cookies.json).
    The cookies file must be present on the server.
    
    Args:
        request: ScrapeRequest containing URL and scraping parameters
        
    Returns:
        ScrapeResponse with scraped posts data
        
    Raises:
        HTTPException: If scraping fails or request is invalid
    """
    try:
        # Force headless mode in Docker/containerized environments (no display available)
        # Check if we're running in a container
        is_container = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'
        effective_headless = request.headless if not is_container else True
        
        if is_container and not request.headless:
            logger.warning("headless=False requested but running in container. Forcing headless=True")
        
        logger.info(f"Received scrape request for URL: {request.url}")
        logger.info(f"Parameters: max_scroll={request.max_scroll}, scroll_delay={request.scroll_delay}, headless={effective_headless} (requested: {request.headless}, container: {is_container})")
        logger.info(f"Using cookies file: {request.cookies_file}")
        
        # Check if cookies file exists
        cookies_file_path = request.cookies_file
        if not os.path.isabs(cookies_file_path):
            # If relative path, make it relative to the app directory
            cookies_file_path = os.path.join(os.path.dirname(__file__), cookies_file_path)
        
        if not os.path.exists(cookies_file_path):
            raise HTTPException(
                status_code=400,
                detail=f"Cookies file not found: {cookies_file_path}. Please ensure the cookies file exists on the server."
            )
        
        # Perform scraping in a subprocess to completely isolate from asyncio event loop
        # This is necessary because Playwright sync API cannot run inside an asyncio loop
        # We use subprocess.Popen instead of ProcessPoolExecutor to avoid Playwright driver issues
        try:
            logger.info("Starting scraping process...")
            # Prepare proxy config if provided
            proxy_config = None
            if request.proxy:
                proxy_config = {
                    'server': request.proxy.server
                }
                if request.proxy.username and request.proxy.password:
                    proxy_config['username'] = request.proxy.username
                    proxy_config['password'] = request.proxy.password
            
            args_dict = {
                'cookies_file': cookies_file_path,
                'url': str(request.url),
                'max_scroll': request.max_scroll,
                'scroll_delay': request.scroll_delay,
                'headless': effective_headless,
                'proxy': proxy_config
            }
            
            # Use subprocess instead of ProcessPoolExecutor to avoid Playwright issues
            # ProcessPoolExecutor can cause Playwright's driver process to hang
            logger.info("Starting scraping subprocess...")
            logger.info(f"Waiting for scraping to complete (timeout: {timeout_seconds}s = {timeout_seconds/60:.1f} minutes)...")
            result = await run_scraping_in_subprocess('scrape_posts', args_dict, timeout_seconds)
            posts = result.get('posts', [])
            logger.info(f"Scraping completed. Found {len(posts) if posts else 0} posts.")
        except asyncio.TimeoutError as te:
            if request.max_scroll >= 25:
                estimated_time_per_scroll = 50  # Very generous: 50 seconds per scroll for high counts
            elif request.max_scroll >= 20:
                estimated_time_per_scroll = request.scroll_delay + 12
            else:
                estimated_time_per_scroll = request.scroll_delay + 8
            calculated_timeout = (request.max_scroll * estimated_time_per_scroll) + 300
            timeout_seconds = max(300, min(calculated_timeout, 1800))
            timeout_minutes = timeout_seconds / 60
            logger.error(f"Scraping timed out after {timeout_minutes:.1f} minutes")
            raise HTTPException(
                status_code=504,
                detail={
                    "error": "Scraping timeout",
                    "message": f"The scraping operation took too long and timed out after {timeout_minutes:.1f} minutes. Try reducing max_scroll or scroll_delay parameters, or check logs for browser initialization issues."
                }
            )
        except Exception as e:
            error_msg = str(e)
            error_details = traceback.format_exc()
            logger.error(f"Scraping failed: {error_msg}")
            logger.error(f"Error details: {error_details}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Scraping failed",
                    "message": error_msg,
                    "details": error_details
                }
            )
        
        # Validate and format response
        if not posts:
            return ScrapeResponse(
                success=True,
                posts=[],
                count=0,
                message="Scraping completed but no posts were found. This may indicate invalid cookies, incorrect URL, or LinkedIn structure changes."
            )
        
        # Convert posts to response format
        formatted_posts = []
        for post in posts:
            formatted_posts.append(PostData(
                text=post.get('text', ''),
                name=post.get('name', ''),
                profile_link=post.get('profile_link', ''),
                job_application_link=post.get('job_application_link', ''),
                post_link=post.get('post_link', ''),
                image_links=post.get('image_links', []),
                comments=post.get('comments', [])
            ))
        
        return ScrapeResponse(
            success=True,
            posts=formatted_posts,
            count=len(formatted_posts),
            message=f"Successfully scraped {len(formatted_posts)} posts"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error occurred",
                "message": str(e),
                "details": error_details
            }
        )


@app.post("/scrape-comments", response_model=ScrapeCommentsResponse)
async def scrape_post_comments(
    request: ScrapeCommentsRequest,
    api_key_verified: bool = Depends(verify_api_key)
):
    """
    Scrape comments from a specific LinkedIn post URL.
    
    Note: Cookies are loaded from a local JSON file on the server (default: linkedin_cookies.json).
    The cookies file must be present on the server.
    
    Args:
        request: ScrapeCommentsRequest containing post URL and parameters
        
    Returns:
        ScrapeCommentsResponse with comments data
        
    Raises:
        HTTPException: If scraping fails or request is invalid
    """
    try:
        # Force headless mode in Docker/containerized environments (no display available)
        is_container = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'
        effective_headless = request.headless if not is_container else True
        
        if is_container and not request.headless:
            logger.warning("headless=False requested but running in container. Forcing headless=True")
            
        logger.info(f"Received scrape-comments request for URL: {request.post_url}")
        logger.info(f"Parameters: max_comments={request.max_comments}, headless={effective_headless} (requested: {request.headless}, container: {is_container})")
        logger.info(f"Using cookies file: {request.cookies_file}")
        
        # Check if cookies file exists
        cookies_file_path = request.cookies_file
        if not os.path.isabs(cookies_file_path):
            cookies_file_path = os.path.join(os.path.dirname(__file__), cookies_file_path)
            
        if not os.path.exists(cookies_file_path):
            raise HTTPException(
                status_code=400,
                detail=f"Cookies file not found: {cookies_file_path}. Please ensure the cookies file exists on the server."
            )
            
        try:
            logger.info("Starting scraping process for comments...")
            args_dict = {
                'cookies_file': cookies_file_path,
                'url': str(request.post_url),
                'max_comments': request.max_comments,
                'headless': effective_headless
            }
            
            # Calculate timeout: 5 minutes base + 10s per comment, capped between 5 and 15 minutes
            timeout_seconds = max(300, min(300 + (request.max_comments * 10), 900))
            
            logger.info("Starting scraping subprocess...")
            result = await run_scraping_in_subprocess('scrape_comments', args_dict, timeout_seconds)
            comments = result.get('comments', [])
            logger.info(f"Scraping completed. Found {len(comments) if comments else 0} comments.")
        except asyncio.TimeoutError as te:
            logger.error(f"Scraping comments timed out")
            raise HTTPException(
                status_code=504,
                detail={
                    "error": "Scraping timeout",
                    "message": "The scraping operation took too long and timed out. Try reducing max_comments parameter."
                }
            )
        except Exception as e:
            error_msg = str(e)
            error_details = traceback.format_exc()
            logger.error(f"Scraping comments failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Scraping failed",
                    "message": error_msg,
                    "details": error_details
                }
            )
            
        # Convert comments to response format
        formatted_comments = []
        for c in comments:
            formatted_comments.append(CommentData(
                commenter_name=c.get('commenter_name', ''),
                commenter_profile_link=c.get('commenter_profile_link', ''),
                comment_text=c.get('comment_text', '')
            ))
            
        return ScrapeCommentsResponse(
            success=True,
            comments=formatted_comments,
            count=len(formatted_comments),
            message=f"Successfully scraped {len(formatted_comments)} comments"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error occurred",
                "message": str(e),
                "details": error_details
            }
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "LinkedIn Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "scrape": "/scrape (POST)",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up the process pool executor on shutdown."""
    if hasattr(app.state, 'scraper_executor'):
        app.state.scraper_executor.shutdown(wait=True)


if __name__ == "__main__":
    import uvicorn
    # Increase timeout for long-running scraping requests (30 minutes)
    # These timeouts control HTTP connection keep-alive, not the scraping operation itself
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        timeout_keep_alive=1800,  # 30 minutes - allow long-running requests
        timeout_graceful_shutdown=300  # 5 minutes for graceful shutdown
    )


