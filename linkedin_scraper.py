#!/usr/bin/env python3
"""
LinkedIn Post Scraper
Scrapes LinkedIn posts from search results and extracts:
- Post text
- Job application links (if available)
- Profile link of the poster
- Image links (if available)
- Name of the poster
"""

import json
import sys
import time
import platform
import signal
import random
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Browser, Page, Cookie


class LinkedInScraper:
    def __init__(self, cookies: List[Dict] = None):
        """
        Initialize the LinkedIn scraper with cookies.
        
        Args:
            cookies: List of cookie dictionaries with keys: name, value, domain, path, etc.
        """
        if cookies:
            self.cookies = self._normalize_cookies(cookies)
        else:
            self.cookies = []
        self.posts_data = []
    
    def load_cookies_from_file(self, cookie_file: str):
        """
        Load cookies from a JSON file.
        
        Args:
            cookie_file: Path to JSON file containing cookies
        """
        try:
            with open(cookie_file, 'r') as f:
                raw_cookies = json.load(f)
            # Normalize cookies for Playwright
            self.cookies = self._normalize_cookies(raw_cookies)
            print(f"Loaded {len(self.cookies)} cookies from {cookie_file}")
        except FileNotFoundError:
            print(f"Cookie file {cookie_file} not found!")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Invalid JSON in cookie file {cookie_file}!")
            sys.exit(1)
    
    def _normalize_cookies(self, cookies: List[Dict]) -> List[Dict]:
        """
        Normalize cookies to Playwright's expected format.
        
        Args:
            cookies: List of cookie dictionaries
            
        Returns:
            List of normalized cookie dictionaries
        """
        normalized = []
        for cookie in cookies:
            normalized_cookie = {
                'name': cookie.get('name', ''),
                'value': cookie.get('value', ''),
                'domain': cookie.get('domain', ''),
                'path': cookie.get('path', '/'),
            }
            
            # Handle expirationDate vs expires
            if 'expirationDate' in cookie and cookie['expirationDate']:
                normalized_cookie['expires'] = int(cookie['expirationDate'])
            elif 'expires' in cookie:
                normalized_cookie['expires'] = cookie['expires']
            # If no expiration, don't include expires field (session cookie)
            
            # Handle httpOnly
            if 'httpOnly' in cookie:
                normalized_cookie['httpOnly'] = bool(cookie['httpOnly'])
            
            # Handle secure
            if 'secure' in cookie:
                normalized_cookie['secure'] = bool(cookie['secure'])
            
            # Normalize sameSite - Playwright expects "Strict", "Lax", or "None"
            same_site_value = cookie.get('sameSite')
            if same_site_value is None:
                # If sameSite is None or missing, default to "None"
                normalized_cookie['sameSite'] = 'None'
            else:
                # Convert to string and lowercase for comparison
                same_site = str(same_site_value).lower()
                if same_site in ['no_restriction', 'none', 'unspecified', '']:
                    normalized_cookie['sameSite'] = 'None'
                elif same_site == 'lax':
                    normalized_cookie['sameSite'] = 'Lax'
                elif same_site == 'strict':
                    normalized_cookie['sameSite'] = 'Strict'
                else:
                    # Default to None if unknown value
                    normalized_cookie['sameSite'] = 'None'
            
            # Only add cookies with required fields
            if normalized_cookie['name'] and normalized_cookie['value'] and normalized_cookie['domain']:
                normalized.append(normalized_cookie)
        
        return normalized
    
    def scrape_posts(self, url: str, max_scroll: int = 5, scroll_delay: int = 2, headless: bool = False, proxy: Optional[Dict] = None) -> List[Dict]:
        """
        Scrape LinkedIn posts from the given URL.
        
        Args:
            url: LinkedIn search results URL
            max_scroll: Maximum number of scrolls to load more posts
            scroll_delay: Delay between scrolls in seconds
            headless: Run browser in headless mode (default: False)
            proxy: Optional proxy configuration dict with 'server' key (e.g., {'server': 'http://proxy:port'})
            
        Returns:
            List of dictionaries containing post data
        """
        print("SCRAPER: Starting scrape_posts method", flush=True)
        print(f"SCRAPER: Parameters - url={url[:50]}..., max_scroll={max_scroll}, scroll_delay={scroll_delay}, headless={headless}", flush=True)
        
        print("SCRAPER: About to start sync_playwright context...", flush=True)
        import os
        
        # Ensure PLAYWRIGHT_BROWSERS_PATH is set correctly
        browsers_path = os.path.expanduser('~/.cache/ms-playwright')
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path
        print(f"SCRAPER: PLAYWRIGHT_BROWSERS_PATH={browsers_path}", flush=True)
        print(f"SCRAPER: Checking if browsers exist at {browsers_path}...", flush=True)
        
        # Check if browser exists
        chromium_path = os.path.join(browsers_path, 'chromium-1091', 'chrome-linux', 'chrome')
        if os.path.exists(chromium_path):
            print(f"SCRAPER: Chromium found at {chromium_path}", flush=True)
        else:
            print(f"SCRAPER: WARNING - Chromium not found at {chromium_path}", flush=True)
            # Try to find any chromium installation
            import glob
            chromium_dirs = glob.glob(os.path.join(browsers_path, 'chromium-*'))
            if chromium_dirs:
                print(f"SCRAPER: Found chromium directories: {chromium_dirs}", flush=True)
            else:
                print(f"SCRAPER: ERROR - No chromium installation found!", flush=True)
        
        try:
            print("SCRAPER: Calling sync_playwright()...", flush=True)
            sys.stdout.flush()
            sys.stderr.flush()
            
            # Import here to ensure it's fresh in this process
            from playwright.sync_api import sync_playwright
            
            print("SCRAPER: About to enter sync_playwright context...", flush=True)
            sys.stdout.flush()
            sys.stderr.flush()
            
            with sync_playwright() as p:
                print("SCRAPER: sync_playwright context started successfully", flush=True)
                sys.stdout.flush()
                # Try Firefox first for non-headless mode (more stable on macOS)
                # Fallback to Chromium if Firefox fails
                browser = None
                browser_type = None
                
                # Try Firefox first (better for non-headless on macOS)
                firefox_launched = False
                if not headless:
                    try:
                        print(f"SCRAPER: Attempting to launch Firefox browser (headless={headless})...", flush=True)
                        browser = p.firefox.launch(headless=headless)
                        browser_type = 'firefox'
                        firefox_launched = True
                        print("SCRAPER: Firefox browser launched successfully", flush=True)
                    except Exception as firefox_error:
                        print(f"SCRAPER: Firefox launch failed: {str(firefox_error)}", flush=True)
                        print("SCRAPER: Trying Chromium...", flush=True)
                
                # Try Chromium if Firefox failed or if headless mode
                if not browser:
                    try:
                        print(f"SCRAPER: Attempting to launch Chromium browser (headless={headless})...", flush=True)
                        launch_args = {
                            'headless': headless,
                            'slow_mo': 100,  # Add small delay between operations for stability
                            'args': [
                                '--no-sandbox',
                                '--disable-setuid-sandbox',
                                '--disable-blink-features=AutomationControlled',
                                '--disable-dev-shm-usage'
                            ]
                        }
                        # In headless mode, we don't need some of these args
                        if headless:
                            launch_args['args'].extend(['--disable-gpu', '--disable-software-rasterizer'])
                        
                        print(f"SCRAPER: Launch args: {launch_args}", flush=True)
                        if proxy:
                            print(f"SCRAPER: Using proxy: {proxy.get('server', 'N/A')}", flush=True)
                        print("SCRAPER: Calling p.chromium.launch()...", flush=True)
                        browser = p.chromium.launch(**launch_args)
                        browser_type = 'chromium'
                        print("SCRAPER: Chromium browser launched successfully", flush=True)
                    except Exception as chromium_error:
                        print(f"SCRAPER: Chromium launch failed: {str(chromium_error)}", flush=True)
                        # If Firefox also failed and we're in non-headless, try Firefox again
                        if not headless:
                            print("SCRAPER: Retrying Firefox...", flush=True)
                            try:
                                browser = p.firefox.launch(headless=headless)
                                browser_type = 'firefox'
                                print("SCRAPER: Firefox browser launched successfully on retry", flush=True)
                            except:
                                pass
                        
                        # Last resort: WebKit
                        if not browser:
                            print("SCRAPER: Trying WebKit as last resort...", flush=True)
                            try:
                                browser = p.webkit.launch(headless=headless)
                                browser_type = 'webkit'
                                print("SCRAPER: WebKit browser launched successfully", flush=True)
                            except Exception as webkit_error:
                                print(f"SCRAPER: All browsers failed to launch!", flush=True)
                                print(f"SCRAPER: Chromium error: {str(chromium_error)}", flush=True)
                                print(f"SCRAPER: WebKit error: {str(webkit_error)}", flush=True)
                                raise Exception("Could not launch any browser. Please check Playwright installation.")
                
                if not browser:
                    raise Exception("Browser launch failed")
                
                try:
                    # Create browser context
                    print("Creating browser context...", flush=True)
                    # Set appropriate user agent based on browser type and OS
                    os_name = platform.system().lower()
                    if browser_type == 'firefox':
                        if os_name == 'windows':
                            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
                        elif os_name == 'linux':
                            user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0'
                        else:  # macOS
                            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0'
                    else:  # Chromium
                        if os_name == 'windows':
                            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                        elif os_name == 'linux':
                            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                        else:  # macOS
                            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    
                    context_options = {
                        'user_agent': user_agent,
                        'viewport': {'width': 1920, 'height': 1080},
                        'ignore_https_errors': True
                    }
                    
                    # Add proxy if provided
                    if proxy:
                        # Playwright proxy format: server must be in format "http://host:port" or "socks5://host:port"
                        proxy_server = proxy.get('server', '')
                        if not proxy_server.startswith('http://') and not proxy_server.startswith('https://') and not proxy_server.startswith('socks5://'):
                            proxy_server = f"http://{proxy_server}"
                        
                        proxy_config = {
                            'server': proxy_server
                        }
                        
                        # Add authentication if provided
                        if proxy.get('username') and proxy.get('password'):
                            proxy_config['username'] = proxy.get('username')
                            proxy_config['password'] = proxy.get('password')
                        
                        context_options['proxy'] = proxy_config
                        print(f"SCRAPER: Browser context will use proxy: {proxy_config['server']}", flush=True)
                        if proxy_config.get('username'):
                            print(f"SCRAPER: Proxy authentication: {proxy_config['username']}", flush=True)
                    
                    context = browser.new_context(**context_options)
                    print("Browser context created", flush=True)
                    
                    # Create page
                    print("Creating page...", flush=True)
                    page = context.new_page()
                    print("Page created successfully", flush=True)
                    
                    # Add cookies BEFORE navigating (critical for proxy scenarios)
                    if self.cookies:
                        try:
                            print(f"Adding {len(self.cookies)} cookies to context BEFORE navigation...", flush=True)
                            # First navigate to LinkedIn domain to establish context
                            page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=30000)
                            time.sleep(1)
                            
                            # Now add cookies
                            context.add_cookies(self.cookies)
                            cookies_check = context.cookies()
                            li_at_present = any(c.get('name') == 'li_at' for c in cookies_check)
                            print(f"Successfully added {len(cookies_check)} cookies to browser context (li_at: {li_at_present})", flush=True)
                            
                            # Reload page to apply cookies
                            page.reload(wait_until='domcontentloaded', timeout=30000)
                            time.sleep(2)
                            
                            # Check if we're still logged in after reload
                            current_url = page.url
                            if '/login' in current_url or '/checkpoint' in current_url or '/authwall' in current_url:
                                print(f"⚠️ WARNING: After adding cookies, redirected to: {current_url[:100]}", flush=True)
                                print("⚠️ Cookies may be invalid or expired. LinkedIn is requiring re-authentication.", flush=True)
                                # Continue anyway - might work after navigating to target URL
                            else:
                                print("✅ Cookies applied successfully - still on LinkedIn domain", flush=True)
                        except Exception as cookie_error:
                            error_str = str(cookie_error)
                            print(f"Warning: Error adding cookies: {error_str}", flush=True)
                            # If it's a navigation error, try to continue
                            if 'ERR_TUNNEL_CONNECTION_FAILED' in error_str or 'TUNNEL' in error_str:
                                if proxy:
                                    raise Exception(f"❌ PROXY CONNECTION FAILED: Cannot connect to proxy server {proxy.get('server', 'N/A')}. Error: {error_str}")
                            print("Continuing without cookies...", flush=True)
                    else:
                        # No cookies provided - navigate to LinkedIn first
                        print("No cookies provided. Navigating to LinkedIn...", flush=True)
                        try:
                            response = page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=30000)
                            current_url = page.url
                            print(f"Initial navigation response: {response.status if response else 'None'}, URL: {current_url[:100]}", flush=True)
                            
                            # Check if we got an error page
                            if current_url.startswith('chrome-error://') or current_url.startswith('about:error'):
                                error_msg = f"Initial navigation failed - got error page: {current_url}"
                                if proxy:
                                    raise Exception(f"Proxy connection issue. Error: {error_msg}")
                                raise Exception(error_msg)
                            
                            print("Successfully navigated to LinkedIn", flush=True)
                            time.sleep(2)
                        except Exception as nav_error:
                            error_str = str(nav_error)
                            print(f"ERROR during initial navigation: {error_str}", flush=True)
                            if proxy:
                                if 'ERR_TUNNEL_CONNECTION_FAILED' in error_str or 'TUNNEL' in error_str:
                                    raise Exception(f"❌ PROXY CONNECTION FAILED: Cannot connect to proxy server {proxy.get('server', 'N/A')}. Error: {error_str}")
                            raise
                    
                    # Now navigate to the actual target URL
                    print(f"Navigating to target URL: {url}", flush=True)
                    navigation_success = False
                    max_retries = 3
                    
                    for attempt in range(max_retries):
                        try:
                            # Use 'domcontentloaded' instead of 'networkidle' - LinkedIn has continuous network activity
                            print(f"SCRAPER: Navigation attempt {attempt + 1}/{max_retries} to: {url[:100]}", flush=True)
                            response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
                            current_url = page.url
                            print(f"SCRAPER: Navigation response status: {response.status if response else 'None'}", flush=True)
                            print(f"SCRAPER: Final URL after navigation: {current_url}", flush=True)
                            
                            # Check if we're on an error page
                            if current_url.startswith('chrome-error://') or current_url.startswith('about:error'):
                                print(f"⚠️ Navigation resulted in error page: {current_url}", flush=True)
                                if attempt < max_retries - 1:
                                    print(f"Retrying navigation (attempt {attempt + 2}/{max_retries})...", flush=True)
                                    time.sleep(3)
                                    continue
                                else:
                                    raise Exception(f"Navigation failed - ended up on error page: {current_url}")
                            
                            # Check if we're on LinkedIn domain
                            if 'linkedin.com' not in current_url:
                                print(f"⚠️ Not on LinkedIn domain: {current_url}", flush=True)
                                if attempt < max_retries - 1:
                                    print(f"Retrying navigation (attempt {attempt + 2}/{max_retries})...", flush=True)
                                    time.sleep(3)
                                    continue
                                else:
                                    raise Exception(f"Navigation failed - not on LinkedIn domain: {current_url}")
                            
                            print(f"✅ Successfully navigated to target URL: {current_url[:100]}", flush=True)
                            navigation_success = True
                            break
                            
                        except Exception as nav_error:
                            error_str = str(nav_error)
                            print(f"Navigation error (attempt {attempt + 1}/{max_retries}): {error_str}", flush=True)
                            
                            if attempt < max_retries - 1:
                                print(f"Retrying navigation in 3 seconds...", flush=True)
                                time.sleep(3)
                                continue
                            else:
                                # Last attempt - check current URL
                                try:
                                    current_url = page.url
                                    print(f"Final URL check: {current_url}", flush=True)
                                    
                                    # If we're on an error page, fail
                                    if current_url.startswith('chrome-error://') or current_url.startswith('about:error'):
                                        raise Exception(f"Navigation failed - ended up on error page: {current_url}")
                                    
                                    # If we're on LinkedIn domain, continue anyway
                                    if 'linkedin.com' in current_url:
                                        print("On LinkedIn domain. Continuing with scraping despite error...", flush=True)
                                        navigation_success = True
                                        break
                                    else:
                                        raise Exception(f"Navigation failed - not on LinkedIn domain: {current_url}")
                                except Exception as final_error:
                                    raise Exception(f"Navigation failed after {max_retries} attempts: {str(final_error)}")
                    
                    if not navigation_success:
                        raise Exception("Navigation failed - could not reach LinkedIn page")
                    
                    # Check for account selection/login/checkpoint page and handle it
                    print("Checking for account selection/login/checkpoint page...", flush=True)
                    current_url_before = page.url
                    handled = self._handle_account_selection(page)
                    
                    # If we're on a checkpoint/login page, try to wait and see if it redirects
                    if '/checkpoint' in current_url_before or '/login' in current_url_before:
                        print("⚠️ On checkpoint/login page. Waiting to see if cookies allow auto-redirect...", flush=True)
                        time.sleep(5)
                        current_url_after = page.url
                        if current_url_after != current_url_before:
                            print(f"✅ Page redirected from {current_url_before[:80]} to {current_url_after[:80]}", flush=True)
                        else:
                            print(f"⚠️ Still on checkpoint/login page. Cookies may not work with this proxy IP.", flush=True)
                    
                    # Wait for page to settle and React content to render
                    print("Waiting for page content to load...", flush=True)
                    time.sleep(5)
                    
                    # Wait for LinkedIn feed content to appear (React-based)
                    print("Waiting for LinkedIn feed content to render...", flush=True)
                    try:
                        # Wait for any feed-related elements to appear
                        page.wait_for_selector('main, [role="main"], div[class*="scaffold"], div[class*="feed"]', timeout=20000)
                        print("Feed container found, waiting for posts to render...", flush=True)
                        
                        # Wait for network to be mostly idle (LinkedIn loads content via API)
                        try:
                            page.wait_for_load_state('networkidle', timeout=15000)
                            print("Network idle state reached", flush=True)
                        except:
                            print("Network idle timeout, continuing anyway...", flush=True)
                        
                        time.sleep(10)  # Additional wait for React to render posts
                        
                        # Check if we have content by looking for activity URNs in the page
                        activity_count = page.evaluate("""
                            () => {
                                const html = document.documentElement.outerHTML;
                                const matches = html.match(/urn:li:activity:\\d+/g);
                                return matches ? matches.length : 0;
                            }
                        """)
                        print(f"Found {activity_count} activity URNs in page HTML", flush=True)
                        
                    except Exception as e:
                        print(f"Warning: Could not find feed container: {str(e)}", flush=True)
                        print("Continuing anyway...", flush=True)
                        time.sleep(8)
                    
                    # Check if page has content before scrolling
                    try:
                        page_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
                        print(f"Initial page height: {page_height}px", flush=True)
                        if page_height < 500:
                            print("Page height is very small. Waiting more for content to load...", flush=True)
                            time.sleep(8)
                            page_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
                            print(f"Page height after wait: {page_height}px", flush=True)
                    except Exception as e:
                        print(f"Could not check page height: {str(e)}", flush=True)
                    
                    # DIAGNOSTIC: Create diagnostic data structure
                    import os
                    diagnostic_data = {
                        'url': url,
                        'max_scroll': max_scroll,
                        'scroll_delay': scroll_delay,
                        'scrolls': [],
                        'initial_state': {},
                        'final_state': {},
                        'extraction_results': {}
                    }
                    
                    # Scroll to load more posts
                    print(f"\n{'='*60}", flush=True)
                    print(f"SCROLLING: Starting scroll sequence (max_scroll={max_scroll}, scroll_delay={scroll_delay}s)", flush=True)
                    print(f"{'='*60}", flush=True)
                    
                    last_height = 0
                    initial_post_count = 0
                    last_post_count = 0
                    
                    # Count initial posts before scrolling
                    try:
                        initial_post_count = page.evaluate("""
                            () => {
                                const html = document.documentElement.outerHTML;
                                const matches = html.match(/urn:li:activity:\\d+/g);
                                return matches ? matches.length : 0;
                            }
                        """)
                        last_post_count = initial_post_count
                        print(f"INITIAL: Found {initial_post_count} activity URNs in HTML", flush=True)
                        
                        # Save initial state to diagnostic
                        diagnostic_data['initial_state'] = {
                            'activity_urns': initial_post_count,
                            'scroll_y': page.evaluate("window.scrollY || window.pageYOffset"),
                            'page_height': page.evaluate("Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"),
                            'url': page.url
                        }
                    except Exception as e:
                        print(f"WARNING: Could not count initial posts: {str(e)}", flush=True)
                    
                    # Get initial scroll position
                    initial_scroll_y = page.evaluate("window.scrollY || window.pageYOffset")
                    print(f"INITIAL: Scroll position: {initial_scroll_y}px", flush=True)
                    
                    # FORCE scroll loop to execute - don't break early
                    scrolls_completed = 0
                    for i in range(max_scroll):
                        try:
                            print(f"\n{'='*60}", flush=True)
                            print(f"SCROLL {i+1}/{max_scroll} - Starting...", flush=True)
                            print(f"{'='*60}", flush=True)
                            
                            # Get current scroll position and page height BEFORE scroll
                            before_scroll_y = page.evaluate("window.scrollY || window.pageYOffset")
                            before_height = page.evaluate("""
                                () => {
                                    return Math.max(
                                        document.body.scrollHeight,
                                        document.documentElement.scrollHeight,
                                        document.body.offsetHeight,
                                        document.documentElement.offsetHeight
                                    );
                                }
                            """)
                            print(f"BEFORE: Scroll Y: {before_scroll_y}px, Page height: {before_height}px", flush=True)
                            
                            # CRITICAL: LinkedIn search results might use a scrollable container, not just window
                            # Try scrolling the main feed container first, then window
                            print("ATTEMPTING: Scrolling main feed container...", flush=True)
                            scroll_success = page.evaluate("""
                                () => {
                                    // Try to find and scroll the main feed container
                                    var main = document.querySelector('main, [role="main"]');
                                    var feedContainer = document.querySelector('[class*="feed"], [class*="scaffold"]');
                                    
                                    if (main && main.scrollHeight > main.clientHeight) {
                                        // Main has scrollable content
                                        var beforeScroll = main.scrollTop;
                                        main.scrollTop = main.scrollHeight;
                                        var afterScroll = main.scrollTop;
                                        return {method: 'main', scrolled: afterScroll > beforeScroll, before: beforeScroll, after: afterScroll};
                                    } else if (feedContainer && feedContainer.scrollHeight > feedContainer.clientHeight) {
                                        // Feed container has scrollable content
                                        var beforeScroll = feedContainer.scrollTop;
                                        feedContainer.scrollTop = feedContainer.scrollHeight;
                                        var afterScroll = feedContainer.scrollTop;
                                        return {method: 'feed', scrolled: afterScroll > beforeScroll, before: beforeScroll, after: afterScroll};
                                    }
                                    return {method: 'none', scrolled: false};
                                }
                            """)
                            print(f"CONTAINER SCROLL: {scroll_success}", flush=True)
                            time.sleep(0.5)
                            
                            # Also scroll window (LinkedIn might use both)
                            print("ATTEMPTING: Scrolling window...", flush=True)
                            scroll_steps = 5
                            current_scroll = before_scroll_y
                            target_bottom = before_height
                            
                            # Calculate scroll increment
                            scroll_increment = max(500, (target_bottom - current_scroll) // scroll_steps)
                            
                            for step in range(scroll_steps):
                                current_scroll += scroll_increment
                                if current_scroll > target_bottom:
                                    current_scroll = target_bottom
                                
                                page.evaluate(f"window.scrollTo(0, {current_scroll})")
                                time.sleep(0.2)  # Small delay between steps
                            
                            # Final scroll to absolute bottom (ensure we're at the very bottom)
                            final_bottom = page.evaluate("""
                                () => {
                                    return Math.max(
                                        document.body.scrollHeight,
                                        document.documentElement.scrollHeight,
                                        document.body.offsetHeight,
                                        document.documentElement.offsetHeight
                                    );
                                }
                            """)
                            
                            page.evaluate(f"window.scrollTo(0, {final_bottom})")
                            
                            # Wait for scroll to complete
                            time.sleep(0.5)
                            
                            # Verify we scrolled
                            after_scroll_y = page.evaluate("window.scrollY || window.pageYOffset")
                            print(f"SCROLL VERIFICATION: At position {after_scroll_y}px of {final_bottom}px (moved {after_scroll_y - before_scroll_y}px)", flush=True)
                            
                            # If scroll didn't work, try alternative methods
                            if after_scroll_y <= before_scroll_y + 100:  # Allow small margin
                                print(f"WARNING: Scroll position didn't change much! Trying alternative scroll methods...", flush=True)
                                
                                # Method 1: Scroll main content area
                                page.evaluate("""
                                    () => {
                                        const main = document.querySelector('main, [role="main"]');
                                        if (main) {
                                            main.scrollTop = main.scrollHeight;
                                        }
                                    }
                                """)
                                time.sleep(0.5)
                                
                                # Method 2: Scroll window again
                                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                                time.sleep(0.5)
                                
                                # Method 3: Use scrollIntoView on last element
                                page.evaluate("""
                                    () => {
                                        const allElements = document.querySelectorAll('div, article');
                                        if (allElements.length > 0) {
                                            allElements[allElements.length - 1].scrollIntoView({behavior: 'smooth', block: 'end'});
                                        }
                                    }
                                """)
                                time.sleep(1)
                                
                                after_scroll_y = page.evaluate("window.scrollY || window.pageYOffset")
                                print(f"AFTER ALT SCROLL: Scroll Y: {after_scroll_y}px", flush=True)
                            
                            # Wait for content to load - use scroll_delay as base, add random variation
                            random_addition = random.uniform(0, 3.0)  # Reduced from 5 to 3
                            total_wait = scroll_delay + random_addition
                            print(f"WAITING: {total_wait:.2f} seconds (base: {scroll_delay}s + random: {random_addition:.2f}s) for content to load...", flush=True)
                            time.sleep(total_wait)
                            
                            # Small additional scroll to trigger lazy loading
                            scroll_amount = random.randint(200, 500)
                            page.evaluate(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}})")
                            print(f"ADDITIONAL SCROLL: {scroll_amount}px", flush=True)
                            time.sleep(random.uniform(1.0, 2.0))
                            
                            # Check for "Load more" or "See more" buttons (LinkedIn might use pagination)
                            try:
                                load_more_buttons = page.evaluate("""
                                    () => {
                                        var buttons = [];
                                        var allButtons = document.querySelectorAll('button, a[role="button"]');
                                        for (var i = 0; i < allButtons.length; i++) {
                                            var btn = allButtons[i];
                                            var text = (btn.innerText || btn.textContent || '').toLowerCase();
                                            if (text.indexOf('load more') >= 0 || 
                                                text.indexOf('see more') >= 0 || 
                                                text.indexOf('show more') >= 0 ||
                                                text.indexOf('view more') >= 0) {
                                                buttons.push({
                                                    text: text,
                                                    visible: btn.offsetParent !== null
                                                });
                                            }
                                        }
                                        return buttons;
                                    }
                                """)
                                if load_more_buttons and len(load_more_buttons) > 0:
                                    print(f"⚠ FOUND LOAD MORE BUTTONS: {load_more_buttons}", flush=True)
                                    # Try clicking the first visible button
                                    visible_buttons = [b for b in load_more_buttons if b.get('visible')]
                                    if visible_buttons:
                                        print(f"CLICKING: Load more button...", flush=True)
                                        try:
                                            page.evaluate("""
                                                () => {
                                                    var buttons = document.querySelectorAll('button, a[role="button"]');
                                                    for (var i = 0; i < buttons.length; i++) {
                                                        var text = (buttons[i].innerText || buttons[i].textContent || '').toLowerCase();
                                                        if ((text.indexOf('load more') >= 0 || text.indexOf('see more') >= 0) && 
                                                            buttons[i].offsetParent !== null) {
                                                            buttons[i].click();
                                                            return true;
                                                        }
                                                    }
                                                    return false;
                                                }
                                            """)
                                            time.sleep(3)  # Wait for content to load after click
                                        except:
                                            pass
                            except:
                                pass
                            
                            # Wait for LinkedIn's lazy loading to complete
                            print("WAITING: Additional 2 seconds for lazy loading...", flush=True)
                            time.sleep(2)
                            
                            # Check if new content loaded
                            after_height = page.evaluate("""
                                () => {
                                    return Math.max(
                                        document.body.scrollHeight,
                                        document.documentElement.scrollHeight,
                                        document.body.offsetHeight,
                                        document.documentElement.offsetHeight
                                    );
                                }
                            """)
                            
                            height_change = after_height - before_height
                            print(f"HEIGHT CHANGE: {height_change}px (before: {before_height}px, after: {after_height}px)", flush=True)
                            
                            # Count activity URNs to see if more posts loaded
                            try:
                                activity_count = page.evaluate("""
                                    () => {
                                        const html = document.documentElement.outerHTML;
                                        const matches = html.match(/urn:li:activity:\\d+/g);
                                        return matches ? matches.length : 0;
                                    }
                                """)
                                post_increase = activity_count - last_post_count
                                print(f"POST COUNT: {activity_count} activity URNs (increase: +{post_increase} from {last_post_count})", flush=True)
                                
                                if activity_count > last_post_count:
                                    print(f"✓ SUCCESS: New posts detected! Total increased from {last_post_count} to {activity_count}", flush=True)
                                    last_post_count = activity_count
                                else:
                                    print(f"⚠ NO NEW POSTS: Count unchanged at {activity_count}", flush=True)
                            except Exception as count_error:
                                print(f"ERROR: Could not count activity URNs: {str(count_error)}", flush=True)
                            
                            scrolls_completed += 1
                            print(f"COMPLETED: Scroll {i+1}/{max_scroll} finished", flush=True)
                            print(f"{'='*60}\n", flush=True)
                            
                            # Save scroll data to diagnostic
                            scroll_data = {
                                'scroll_number': i + 1,
                                'before_scroll_y': before_scroll_y,
                                'after_scroll_y': after_scroll_y,
                                'before_height': before_height,
                                'after_height': after_height,
                                'height_change': height_change,
                                'activity_urns_before': last_post_count,
                                'activity_urns_after': activity_count if 'activity_count' in locals() else last_post_count,
                                'posts_increased': activity_count > last_post_count if 'activity_count' in locals() else False
                            }
                            diagnostic_data['scrolls'].append(scroll_data)
                            
                            # Continue to next scroll regardless - don't break early
                            # LinkedIn might load content on later scrolls even if this one didn't
                            
                        except Exception as scroll_error:
                            print(f"\nERROR during scroll {i+1}: {str(scroll_error)}", flush=True)
                            import traceback
                            traceback.print_exc()
                            # Try to continue scrolling
                            try:
                                page.evaluate("window.scrollTo(0, document.body.scrollHeight || document.documentElement.scrollHeight)")
                                print(f"RECOVERY: Waiting {scroll_delay} seconds...", flush=True)
                                time.sleep(scroll_delay)
                                scrolls_completed += 1
                            except:
                                print("FATAL: Could not continue scrolling. Continuing to next scroll anyway...", flush=True)
                    
                    print(f"\n{'='*60}", flush=True)
                    print(f"SCROLLING COMPLETE: Executed {scrolls_completed}/{max_scroll} scrolls", flush=True)
                    print(f"FINAL POST COUNT: {last_post_count} activity URNs (started with {initial_post_count})", flush=True)
                    print(f"{'='*60}\n", flush=True)
                    
                    # Save final state to diagnostic
                    try:
                        diagnostic_data['final_state'] = {
                            'activity_urns': last_post_count,
                            'scroll_y': page.evaluate("window.scrollY || window.pageYOffset"),
                            'page_height': page.evaluate("Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"),
                            'scrolls_completed': scrolls_completed,
                            'posts_increased': last_post_count > initial_post_count
                        }
                    except:
                        pass
                    
                    # Final scroll to ensure we're at the very bottom and trigger any remaining lazy loads
                    print("FINAL SCROLL: Ensuring we're at the absolute bottom...", flush=True)
                    try:
                        final_height = page.evaluate("""
                            () => {
                                return Math.max(
                                    document.body.scrollHeight,
                                    document.documentElement.scrollHeight,
                                    document.body.offsetHeight,
                                    document.documentElement.offsetHeight
                                );
                            }
                        """)
                        page.evaluate(f"window.scrollTo(0, {final_height})")
                        time.sleep(2)
                        
                        # Scroll back up a bit then down again to trigger any lazy loading
                        page.evaluate("window.scrollTo(0, " + str(final_height - 1000) + ")")
                        time.sleep(1)
                        page.evaluate(f"window.scrollTo(0, {final_height})")
                        time.sleep(2)
                        
                        # Final count
                        final_activity_count = page.evaluate("""
                            () => {
                                const html = document.documentElement.outerHTML;
                                const matches = html.match(/urn:li:activity:\\d+/g);
                                return matches ? matches.length : 0;
                            }
                        """)
                        print(f"FINAL CHECK: {final_activity_count} activity URNs found in HTML", flush=True)
                    except Exception as final_error:
                        print(f"Error in final scroll: {str(final_error)}", flush=True)
                    
                    # DIAGNOSTIC: Count post containers before extraction
                    print("\n" + "="*60, flush=True)
                    print("DIAGNOSTIC: Counting post containers in DOM...", flush=True)
                    print("="*60, flush=True)
                    try:
                        container_counts = page.evaluate("""
                            () => {
                                var counts = {};
                                
                                // Count by data attributes
                                counts['data-view-name="feed-full-update"'] = document.querySelectorAll('[data-view-name="feed-full-update"]').length;
                                counts['data-view-name="feed-update"'] = document.querySelectorAll('[data-view-name="feed-update"]').length;
                                counts['role="listitem"'] = document.querySelectorAll('[role="listitem"]').length;
                                counts['data-id*="urn:li:activity"'] = document.querySelectorAll('div[data-id*="urn:li:activity"], article[data-id*="urn:li:activity"]').length;
                                
                                // Count activity URNs in HTML
                                var html = document.documentElement.outerHTML;
                                var matches = html.match(/urn:li:activity:\\d+/g);
                                counts['activity_urns_in_html'] = matches ? matches.length : 0;
                                
                                // Count profile links
                                var profileLinks = document.querySelectorAll('a[href*="/in/"][href*="linkedin.com/in"]');
                                var validProfileLinks = 0;
                                for (var i = 0; i < profileLinks.length; i++) {
                                    var href = profileLinks[i].href || profileLinks[i].getAttribute('href') || '';
                                    if (href.indexOf('/opportunities/') < 0 && href.indexOf('/jobs/') < 0) {
                                        validProfileLinks++;
                                    }
                                }
                                counts['valid_profile_links'] = validProfileLinks;
                                
                                // Page dimensions
                                counts['scroll_y'] = window.scrollY || window.pageYOffset;
                                counts['page_height'] = Math.max(
                                    document.body.scrollHeight,
                                    document.documentElement.scrollHeight
                                );
                                counts['viewport_height'] = window.innerHeight;
                                
                                return counts;
                            }
                        """)
                        print(f"DIAGNOSTIC RESULTS:", flush=True)
                        for key, value in container_counts.items():
                            print(f"  {key}: {value}", flush=True)
                        print("="*60 + "\n", flush=True)
                    except Exception as diag_error:
                        print(f"DIAGNOSTIC ERROR: {str(diag_error)}", flush=True)
                    
                    # Wait a bit more for final content to render after scrolling (LinkedIn lazy loads)
                    print("Waiting for final content to render after scrolling...", flush=True)
                    time.sleep(5)  # Increased from 3 to 5 seconds
                    
                    # Extract posts
                    print("Extracting posts...", flush=True)
                    
                    # Debug: Check page content before extraction
                    try:
                        page_title = page.title()
                        current_url = page.url
                        print(f"SCRAPER: Page title: {page_title}", flush=True)
                        print(f"SCRAPER: Current URL: {current_url}", flush=True)
                        
                        # CRITICAL: Check if we're on an error page
                        if current_url.startswith('chrome-error://') or current_url.startswith('about:error'):
                            raise Exception(f"Cannot extract posts - page is on error page: {current_url}. Navigation likely failed.")
                        
                        # Check if we're on LinkedIn domain
                        if 'linkedin.com' not in current_url:
                            raise Exception(f"Cannot extract posts - not on LinkedIn domain: {current_url}")
                        
                        # Check if we're on a login page or blocked (but allow checkpoint if we already tried to bypass)
                        if 'login' in current_url.lower() or ('checkpoint' in current_url.lower() and 'session_redirect' not in current_url) or 'authwall' in current_url.lower():
                            print("SCRAPER: WARNING - Appears to be on login/challenge/authwall page!", flush=True)
                            print(f"SCRAPER: LinkedIn is requiring authentication. This usually means:", flush=True)
                            print(f"SCRAPER: 1) Cookies are invalid/expired", flush=True)
                            print(f"SCRAPER: 2) LinkedIn detected automation and requires re-login", flush=True)
                            print(f"SCRAPER: 3) Proxy IP is flagged by LinkedIn (cookies from different IP)", flush=True)
                            
                            # If we're still on checkpoint after redirect attempt, it's a persistent issue
                            if 'checkpoint' in current_url.lower():
                                raise Exception(f"Cannot extract posts - checkpoint page persists after redirect attempts. Cookies were likely obtained without proxy. Solution: Get fresh cookies while using the same proxy IP ({proxy.get('server', 'N/A') if proxy else 'N/A'}), or use cookies that were obtained with this proxy.")
                            else:
                                raise Exception(f"Cannot extract posts - redirected to login/authwall: {current_url[:150]}. Please update cookies or try a different proxy.")
                        
                        # Check page content
                        body_text = page.evaluate("document.body.innerText || ''")
                        print(f"SCRAPER: Page body text length: {len(body_text)} characters", flush=True)
                        if len(body_text) < 100:
                            print("SCRAPER: WARNING - Page content is very short, may indicate blocking or empty page", flush=True)
                            print(f"SCRAPER: First 200 chars of body: {body_text[:200]}", flush=True)
                            
                            # If body is empty or very short, wait more and check again
                            if len(body_text) < 50:
                                print("SCRAPER: Body text is very short, waiting 5 more seconds for content to load...", flush=True)
                                time.sleep(5)
                                body_text = page.evaluate("document.body.innerText || ''")
                                print(f"SCRAPER: Body text length after wait: {len(body_text)} characters", flush=True)
                                
                                if len(body_text) < 50:
                                    raise Exception("Page content is empty or too short - likely not loaded or blocked")
                    except Exception as debug_error:
                        error_msg = str(debug_error)
                        print(f"SCRAPER: Error during debug check: {error_msg}", flush=True)
                        # Re-raise if it's a critical error
                        if 'error page' in error_msg.lower() or 'not on linkedin' in error_msg.lower() or 'empty' in error_msg.lower():
                            raise
                    
                    # DIAGNOSTIC: Final check before extraction
                    print(f"\n{'='*60}", flush=True)
                    print(f"PRE-EXTRACTION DIAGNOSTIC", flush=True)
                    print(f"{'='*60}", flush=True)
                    try:
                        pre_extract_diag = page.evaluate("""
                            () => {
                                var info = {};
                                
                                // Count post containers
                                info.feed_full_update = document.querySelectorAll('[data-view-name="feed-full-update"]').length;
                                info.feed_update = document.querySelectorAll('[data-view-name="feed-update"]').length;
                                info.listitems = document.querySelectorAll('[role="listitem"]').length;
                                info.activity_divs = document.querySelectorAll('div[data-id*="urn:li:activity"], article[data-id*="urn:li:activity"]').length;
                                
                                // Count activity URNs
                                var html = document.documentElement.outerHTML;
                                var matches = html.match(/urn:li:activity:\\d+/g);
                                info.activity_urns = matches ? matches.length : 0;
                                
                                // Scroll info
                                info.scroll_y = window.scrollY || window.pageYOffset;
                                info.page_height = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
                                info.viewport_height = window.innerHeight;
                                info.is_at_bottom = (info.scroll_y + info.viewport_height) >= (info.page_height - 100);
                                
                                // URL info
                                info.current_url = window.location.href;
                                
                                return info;
                            }
                        """)
                        print(f"PRE-EXTRACTION COUNTS:", flush=True)
                        for key, value in pre_extract_diag.items():
                            print(f"  {key}: {value}", flush=True)
                        print(f"{'='*60}\n", flush=True)
                    except Exception as pre_diag_error:
                        print(f"PRE-EXTRACTION DIAGNOSTIC ERROR: {str(pre_diag_error)}", flush=True)
                    
                    posts = self._extract_posts(page)
                    print(f"\n{'='*60}", flush=True)
                    print(f"EXTRACTION COMPLETE: Found {len(posts)} posts", flush=True)
                    print(f"{'='*60}\n", flush=True)
                    
                    # Save extraction results to diagnostic
                    diagnostic_data['extraction_results'] = {
                        'posts_found': len(posts),
                        'posts_with_name': sum(1 for p in posts if p.get('name')),
                        'posts_with_profile': sum(1 for p in posts if p.get('profile_link')),
                        'posts_with_text': sum(1 for p in posts if p.get('text') and len(p.get('text', '')) > 50)
                    }
                    
                    # Save diagnostic data to file
                    try:
                        diagnostic_file = '/app/scrape_diagnostic.json' if os.path.exists('/app') else 'scrape_diagnostic.json'
                        import json
                        with open(diagnostic_file, 'w', encoding='utf-8') as f:
                            json.dump(diagnostic_data, f, indent=2, ensure_ascii=False)
                        print(f"DIAGNOSTIC: Saved diagnostic data to {diagnostic_file}", flush=True)
                        print(f"  - Scroll data: {len(diagnostic_data.get('scrolls', []))} scrolls recorded", flush=True)
                        print(f"  - Initial URNs: {diagnostic_data.get('initial_state', {}).get('activity_urns', 0)}", flush=True)
                        print(f"  - Final URNs: {diagnostic_data.get('final_state', {}).get('activity_urns', 0)}", flush=True)
                        print(f"  - Posts extracted: {len(posts)}", flush=True)
                    except Exception as diag_save_error:
                        print(f"WARNING: Could not save diagnostic data: {str(diag_save_error)}", flush=True)
                    
                    # If no posts found, provide more debugging info
                    if len(posts) == 0:
                        print("SCRAPER: No posts found. Checking page structure...", flush=True)
                        try:
                            # Check for common LinkedIn selectors
                            selectors_to_check = [
                                'div.feed-shared-update-v2',
                                'div[data-id*="urn:li:activity"]',
                                'article',
                                '.feed-shared-update-v2',
                                '[data-id^="urn:li:activity"]'
                            ]
                            for selector in selectors_to_check:
                                count = page.evaluate(f"document.querySelectorAll('{selector}').length")
                                print(f"SCRAPER: Found {count} elements matching '{selector}'", flush=True)
                        except Exception as selector_error:
                            print(f"SCRAPER: Error checking selectors: {str(selector_error)}", flush=True)
                    
                    return posts
                    
                except Exception as e:
                    print(f"Error during scraping: {str(e)}", flush=True)
                    import traceback
                    traceback.print_exc()
                    raise
                finally:
                    try:
                        if 'browser' in locals() and browser:
                            browser.close()
                            print("Browser closed", flush=True)
                    except:
                        pass
        except Exception as e:
            print(f"SCRAPER: Error starting sync_playwright context: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            raise

    def _handle_account_selection(self, page: Page) -> bool:
        """
        Handle LinkedIn account selection/login page if present.
        Automatically clicks on the first available account.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if account was selected, False otherwise
        """
        try:
            time.sleep(2)  # Wait for page to load
            current_url = page.url
            page_title = page.title().lower()
            
            # Check if we're on account selection/login/checkpoint page
            is_account_selection = (
                'checkpoint' in current_url.lower() or
                'login' in current_url.lower() or
                'login' in page_title or
                'sign in' in page_title or
                'welcome back' in page_title or
                'challenge' in current_url.lower()
            )
            
            if is_account_selection:
                print("\n" + "="*60)
                print("⚠️  ACCOUNT SELECTION PAGE DETECTED")
                print("="*60)
                print(f"Current URL: {current_url}")
                print(f"Page title: {page_title}")
                print("Attempting to automatically select account...")
                
                # Wait a bit for the page to fully render
                time.sleep(3)
                
                # Strategy 1: Look for the main account selection element
                # LinkedIn shows the primary account as a large clickable card/button
                account_found = False
                
                # Try specific LinkedIn selectors first
                specific_selectors = [
                    'button[data-test-id*="account"]',  # LinkedIn test IDs
                    'div[data-test-id*="account"]',
                    'button:has-text("Vishu")',  # Try to find by name if visible
                    'div:has-text("Vishu")',
                ]
                
                for selector in specific_selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        if elements:
                            for elem in elements[:1]:  # Try first element only
                                try:
                                    if elem.is_visible():
                                        print(f"Found account element using selector: {selector}")
                                        elem.scroll_into_view_if_needed()
                                        time.sleep(1)
                                        elem.click()
                                        print("✅ Clicked account element")
                                        account_found = True
                                        time.sleep(3)
                                        break
                                except:
                                    continue
                            if account_found:
                                break
                    except:
                        continue
                
                # If specific selectors didn't work, try generic approach
                if not account_found:
                    # Get all buttons and divs with role="button"
                    clickables = page.query_selector_all('button, div[role="button"], a[href*="checkpoint"]')
                    # Filter to find the main account selector (usually the first large one)
                    for elem in clickables:
                        try:
                            if elem.is_visible():
                                text = elem.inner_text().strip().lower()
                                # Skip "Sign in using another account" and navigation elements
                                if (text and 
                                    'another account' not in text and 
                                    'sign in using' not in text and
                                    'join now' not in text and
                                    len(text) > 0):
                                    # Check element size - account cards are usually larger
                                    box = elem.bounding_box()
                                    if box and box['height'] > 50:  # Account cards are usually tall
                                        print(f"Found large clickable element (likely account card). Clicking...")
                                        elem.scroll_into_view_if_needed()
                                        time.sleep(1)
                                        elem.click()
                                        print("✅ Clicked account element")
                                        account_found = True
                                        time.sleep(3)
                                        break
                        except:
                            continue
                
                # Strategy 2: Look for the main account card/button (usually the first large clickable element)
                if not account_found:
                    try:
                        print("Trying alternative: Looking for main account card...")
                        # LinkedIn account selection usually has a main card with the account info
                        # Look for elements containing profile info that are clickable
                        account_cards = page.query_selector_all('div[class*="account"], div[class*="identity"], div[class*="profile-card"]')
                        for card in account_cards:
                            try:
                                if card.is_visible():
                                    # Check if it has clickable children or is itself clickable
                                    clickable = card.query_selector('button, a, [role="button"]')
                                    if not clickable:
                                        # Try clicking the card itself if it's interactive
                                        try:
                                            card.scroll_into_view_if_needed()
                                            time.sleep(1)
                                            card.click()
                                            print("✅ Clicked account card")
                                            account_found = True
                                            time.sleep(3)
                                            break
                                        except:
                                            pass
                                    else:
                                        clickable.scroll_into_view_if_needed()
                                        time.sleep(1)
                                        clickable.click()
                                        print("✅ Clicked account via card button")
                                        account_found = True
                                        time.sleep(3)
                                        break
                            except:
                                continue
                    except:
                        pass
                
                # Strategy 3: Look for any clickable element that's not "Sign in using another account"
                if not account_found:
                    try:
                        print("Trying alternative: Looking for main account button...")
                        # Get all clickable elements
                        clickables = page.query_selector_all('button, a, div[role="button"], [onclick]')
                        for elem in clickables:
                            try:
                                if elem.is_visible():
                                    text = elem.inner_text().strip().lower()
                                    # Skip "Sign in using another account" and similar
                                    if text and 'another account' not in text and 'sign in using' not in text:
                                        # Check if it looks like an account selector (has some text but not too much)
                                        if len(text) > 0 and len(text) < 200:
                                            print(f"Found clickable element: {text[:50]}... Clicking...")
                                            elem.scroll_into_view_if_needed()
                                            time.sleep(1)
                                            elem.click()
                                            print("✅ Clicked element")
                                            account_found = True
                                            time.sleep(3)
                                            break
                            except:
                                continue
                    except:
                        pass
                
                if account_found:
                    # Wait for navigation away from login page
                    print("Waiting for navigation after account selection...")
                    for i in range(10):  # Wait up to 10 seconds
                        time.sleep(1)
                        new_url = page.url
                        new_title = page.title().lower()
                        if ('checkpoint' not in new_url.lower() and 
                            'login' not in new_url.lower() and
                            'login' not in new_title and
                            'sign in' not in new_title):
                            print(f"✅ Successfully navigated away from login page!")
                            print(f"New URL: {new_url}")
                            return True
                    print("⚠️  Still on login page after click. Waiting 5 more seconds...")
                    time.sleep(5)
                else:
                    print("⚠️  Could not automatically select account.")
                    print("Please manually click on your account in the browser window.")
                    print("Waiting 15 seconds for manual selection...")
                    # Wait for manual selection
                    initial_url = page.url
                    for i in range(15):
                        time.sleep(1)
                        current_url = page.url
                        if current_url != initial_url and 'checkpoint' not in current_url.lower():
                            print("✅ Account selected manually!")
                            return True
                    print("⚠️  Timeout waiting for account selection.")
                
                print("="*60 + "\n")
                return account_found
                
        except Exception as e:
            print(f"Error handling account selection: {str(e)}")
            print("Continuing anyway...")
            return False
    
    def _extract_posts(self, page: Page) -> List[Dict]:
        """
        Extract post data from the current page.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of post dictionaries
        """
        import json
        from datetime import datetime
        import os
        
        posts = []
        log_path = '/app/.cursor/debug.log' if os.path.exists('/app') else '/Users/vishu/Documents/linkedin_scraper/.cursor/debug.log'
        
        # #region agent log
        try:
            with open(log_path, 'a') as log_file:
                log_file.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H1",
                    "location": "linkedin_scraper.py:_extract_posts",
                    "message": "Starting post extraction",
                    "data": {"timestamp": int(datetime.now().timestamp() * 1000)},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except: pass
        # #endregion
        
        # Wait for content to load
        try:
            page.wait_for_selector('body', timeout=10000)
            # Additional wait for React content to render
            time.sleep(3)
        except:
            pass
        
        # Check page state before extraction
        try:
            page_url = page.url
            page_title = page.title()
            body_text_length = len(page.evaluate("document.body.innerText || ''"))
            
            # #region agent log
            try:
                with open(log_path, 'a') as log_file:
                    log_file.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "H2",
                        "location": "linkedin_scraper.py:_extract_posts",
                        "message": "Page state before extraction",
                        "data": {
                            "url": page_url,
                            "title": page_title,
                            "body_text_length": body_text_length,
                            "is_login": "/login" in page_url or "/authwall" in page_url,
                            "is_search": "/search" in page_url
                        },
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + "\n")
            except: pass
            # #endregion
            
            print(f"SCRAPER: Page URL: {page_url[:150]}", flush=True)
            print(f"SCRAPER: Page title: {page_title[:80]}", flush=True)
            print(f"SCRAPER: Body text length: {body_text_length} chars", flush=True)
        except Exception as e:
            print(f"SCRAPER: Error checking page state: {str(e)}", flush=True)
        
        # LinkedIn post containers - updated for current LinkedIn structure
        # Try multiple selectors to find posts (React-based structure)
        post_selectors = [
            'div[data-id*="urn:li:activity"]',
            'div[data-urn*="urn:li:activity"]',
            'article[data-id*="urn:li:activity"]',
            'div.feed-shared-update-v2',
            'div[class*="feed-shared-update-v2"]',
            'div[class*="update-components-actor"]',
            'div[class*="update-components"]',
            'article[class*="update-components"]',
            'div[class*="feed-shared-update-v2__description"]',
            'div[class*="feed-shared-update"]',
            'article[data-id]',
            'div[role="article"]',
            'section[class*="feed"] > div > div',
            'main div[class*="scaffold"] div[class*="feed"] > div'
        ]
        
        post_elements = []
        selector_results = {}
        
        for selector in post_selectors:
            try:
                elements = page.query_selector_all(selector)
                count = len(elements) if elements else 0
                selector_results[selector] = count
                
                # #region agent log
                try:
                    with open(log_path, 'a') as log_file:
                        log_file.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "H3",
                            "location": "linkedin_scraper.py:_extract_posts",
                            "message": "Selector check result",
                            "data": {"selector": selector, "count": count},
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + "\n")
                except: pass
                # #endregion
                
                if elements and len(elements) > 0:
                    post_elements = elements
                    print(f"Found {len(elements)} posts using selector: {selector}", flush=True)
                    break
            except Exception as e:
                selector_results[selector] = f"error: {str(e)}"
                print(f"Error with selector {selector}: {str(e)}", flush=True)
                continue
        
        if not post_elements:
            # Fallback: try to find any post-like elements by looking for common patterns
            if not post_elements:
                fallback_selectors = [
                    'div[class*="feed"] > div',
                    'main div[class*="scaffold"] > div > div',
                    'section[class*="feed"] > div',
                    'div[class*="feed"]',
                    'article',
                    'div[role="article"]',
                    'div[class*="update"]',
                    'div[class*="activity"]'
                ]
                for selector in fallback_selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        count = len(elements) if elements else 0
                        selector_results[selector] = count
                        
                        # #region agent log
                        try:
                            with open(log_path, 'a') as log_file:
                                log_file.write(json.dumps({
                                    "sessionId": "debug-session",
                                    "runId": "run1",
                                    "hypothesisId": "H3",
                                    "location": "linkedin_scraper.py:_extract_posts",
                                    "message": "Fallback selector check",
                                    "data": {"selector": selector, "count": count},
                                    "timestamp": int(datetime.now().timestamp() * 1000)
                                }) + "\n")
                        except: pass
                        # #endregion
                        
                        # Filter elements that might be posts (have substantial text content)
                        if elements and len(elements) > 0:
                            filtered_elements = []
                            for elem in elements:
                                try:
                                    text = elem.inner_text() if hasattr(elem, 'inner_text') else ''
                                    # Only include if it has substantial text (likely a post)
                                    if text and len(text.strip()) > 50:
                                        filtered_elements.append(elem)
                                except:
                                    continue
                            
                            if len(filtered_elements) >= 3:  # Likely posts if we find several with text
                                post_elements = filtered_elements
                                print(f"Using fallback selector: {selector}, found {len(filtered_elements)} elements with content", flush=True)
                                break
                    except Exception as e:
                        selector_results[selector] = f"error: {str(e)}"
                        continue
        
        # #region agent log
        try:
            with open(log_path, 'a') as log_file:
                log_file.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H3",
                    "location": "linkedin_scraper.py:_extract_posts",
                    "message": "Post elements found",
                    "data": {
                        "total_elements": len(post_elements),
                        "selector_results": selector_results
                    },
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except: pass
        # #endregion
        
        if not post_elements:
            print("Warning: No posts found. The page structure may have changed or you may not be logged in.", flush=True)
            # #region agent log
            try:
                with open(log_path, 'a') as log_file:
                    log_file.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "H4",
                        "location": "linkedin_scraper.py:_extract_posts",
                        "message": "No post elements found",
                        "data": {"selector_results": selector_results},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + "\n")
            except: pass
            # #endregion
            
            # Try to save page HTML for debugging
            try:
                html_content = page.content()
                html_length = len(html_content)
                # #region agent log
                try:
                    with open(log_path, 'a') as log_file:
                        log_file.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "H4",
                            "location": "linkedin_scraper.py:_extract_posts",
                            "message": "Page HTML saved for debugging",
                            "data": {"html_length": html_length},
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + "\n")
                except: pass
                # #endregion
                
                debug_file = '/app/debug_page.html' if os.path.exists('/app') else 'debug_page.html'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"Page HTML saved to {debug_file} for inspection (length: {html_length} chars)", flush=True)
            except Exception as e:
                print(f"Error saving debug HTML: {str(e)}", flush=True)
            
            # Try JavaScript-based extraction before giving up
            print("DEBUG: post_elements is empty, attempting JavaScript extraction...", flush=True)
            print("Trying JavaScript-based post detection and extraction...", flush=True)
            try:
                # Use JavaScript to find posts and extract data directly
                # Use a simpler JavaScript approach to avoid quote escaping issues
                js_posts = page.evaluate("""
                    (async function() {
                        var posts = [];
                        var seenPosts = new Set(); // Track unique posts by content hash
                        
                        // CRITICAL: Find actual LinkedIn post containers using data attributes and structure
                        // LinkedIn uses specific data attributes and class patterns for posts
                        var postContainerSelectors = [
                            '[data-view-name="feed-full-update"]',
                            '[data-view-name="feed-update"]',
                            '[role="listitem"]',
                            'div[data-id*="urn:li:activity"]',
                            'article[data-id*="urn:li:activity"]',
                            'div[data-urn*="urn:li:activity"]'
                        ];
                        
                        var postContainers = [];
                        for (var s = 0; s < postContainerSelectors.length; s++) {
                            var containers = document.querySelectorAll(postContainerSelectors[s]);
                            for (var c = 0; c < containers.length; c++) {
                                var container = containers[c];
                                // Exclude navigation/header/footer
                                if (!container.closest('nav, header, footer, [role="navigation"], [role="banner"]')) {
                                    postContainers.push(container);
                                }
                            }
                        }
                        
                        // If no containers found with selectors, fall back to finding by structure
                        if (postContainers.length === 0) {
                            var allDivs = document.querySelectorAll('div, article');
                            for (var d = 0; d < allDivs.length; d++) {
                                var div = allDivs[d];
                                // Check if it looks like a post container
                                var hasActivityUrn = div.getAttribute('data-id') && div.getAttribute('data-id').indexOf('urn:li:activity') >= 0;
                                var hasFeedClasses = div.className && (
                                    div.className.indexOf('feed') >= 0 || 
                                    div.className.indexOf('update') >= 0 ||
                                    div.className.indexOf('post') >= 0
                                );
                                var hasProfileLink = div.querySelector('a[href*="/in/"][href*="linkedin.com/in"]') && 
                                                    !div.querySelector('a[href*="/in/"][href*="linkedin.com/in"]').href.indexOf('/opportunities/') >= 0;
                                var hasSubstantialText = (div.innerText || div.textContent || '').trim().length > 100;
                                
                                if ((hasActivityUrn || hasFeedClasses) && hasProfileLink && hasSubstantialText) {
                                    if (!div.closest('nav, header, footer')) {
                                        postContainers.push(div);
                                    }
                                }
                            }
                        }
                        
                        console.log('Found ' + postContainers.length + ' potential post containers');
                        
                        // DIAGNOSTIC: Log what we found
                        var diagnosticInfo = {
                            total_containers_found: postContainers.length,
                            containers_by_selector: {}
                        };
                        for (var s = 0; s < postContainerSelectors.length; s++) {
                            var selector = postContainerSelectors[s];
                            var count = document.querySelectorAll(selector).length;
                            diagnosticInfo.containers_by_selector[selector] = count;
                        }
                        console.log('DIAGNOSTIC: ' + JSON.stringify(diagnosticInfo));
                        
                        for (var i = 0; i < postContainers.length; i++) {
                            var elem = postContainers[i];
                            try {
                                // Get all text from this container
                                var allText = (elem.innerText || elem.textContent || '').trim();
                                
                                // Skip if too short or too long (likely not a post)
                                if (allText.length < 50 || allText.length > 50000) continue;
                                
                                // Find profile link - MUST be a real profile, not job opportunities
                                var profileLink = '';
                                var actorLink = null;
                                
                                // Find all profile links in the container
                                var allProfileLinks = elem.querySelectorAll('a[href*="/in/"], a[href*="/company/"]');
                                for (var pl = 0; pl < allProfileLinks.length; pl++) {
                                    var link = allProfileLinks[pl];
                                    var href = link.href || link.getAttribute('href') || '';
                                    
                                    // EXCLUDE job opportunity links
                                    if (href.indexOf('/opportunities/') >= 0 || href.indexOf('/jobs/') >= 0) continue;
                                    
                                    // The first link with text is our actor link (author)
                                    var linkText = (link.innerText || '').trim();
                                    if (linkText) {
                                        actorLink = link;
                                        profileLink = href;
                                        break;
                                    }
                                }
                                
                                // Clean profile link
                                if (profileLink) {
                                    if (profileLink.indexOf('?') > 0) {
                                        profileLink = profileLink.substring(0, profileLink.indexOf('?'));
                                    }
                                    if (profileLink.indexOf('#') > 0) {
                                        profileLink = profileLink.substring(0, profileLink.indexOf('#'));
                                    }
                                    if (profileLink.indexOf('http') < 0 && profileLink.indexOf('/') === 0) {
                                        profileLink = 'https://www.linkedin.com' + profileLink;
                                    }
                                }
                                
                                // MUST have a valid profile link to be a post
                                if (!profileLink) continue;
                                
                                // Extract name directly from the actor link text
                                var name = '';
                                if (actorLink) {
                                    var rawNameText = (actorLink.innerText || '').trim();
                                    if (rawNameText) {
                                        name = rawNameText.split('\\n')[0].split('•')[0].split('·')[0].split('Author')[0].split(',')[0].trim();
                                    }
                                }
                                
                                // Clean up text - remove UI elements and filter lines
                                var uiKeywords = [
                                    'Skip to main content', 'Home', 'My Network', 'Jobs', 'Messaging', 
                                    'Notifications', 'Me', 'For Business', 'Try Premium', 'Posts', 
                                    'Sort by', 'Date posted', 'Content type', 'From member', 'All filters',
                                    'Feed post', 'Like', 'Comment', 'Repost', 'Send', 'Follow',
                                    'reactions', 'comments', 'reposts', 'more', 'View job preferences',
                                    'Only connections can comment', 'You can still react or share',
                                    'Are these results helpful?', 'Your feedback helps us improve',
                                    'Latest', 'Past 24 hours', 'Reset', 'View job', 'is open to work',
                                    'Looking for', 'View job preferences'
                                ];
                                
                                var textLines = allText.split('\\n');
                                var cleanLines = [];
                                for (var tl = 0; tl < textLines.length; tl++) {
                                    var line = textLines[tl].trim();
                                    if (!line || line.length < 3) continue;
                                    
                                    // Skip UI keywords
                                    var isUI = false;
                                    for (var uk = 0; uk < uiKeywords.length; uk++) {
                                        if (line === uiKeywords[uk] || line.indexOf(uiKeywords[uk]) === 0) {
                                            isUI = true;
                                            break;
                                        }
                                    }
                                    if (isUI) continue;
                                    
                                    // Skip reaction/comment counts
                                    if (/^\\d+\\s*(reactions?|comments?|reposts?)$/i.test(line)) continue;
                                    
                                    // Skip lines that are just job titles or locations
                                    if (line.indexOf(' at ') >= 0 && line.length < 80) continue;
                                    if (line.indexOf('Developer') >= 0 && line.indexOf('Engineer') >= 0 && line.length < 100) continue;
                                    
                                    cleanLines.push(line);
                                }
                                
                                var cleanText = cleanLines.join('\\n').trim();
                                
                                // Must have substantial clean text
                                if (cleanText.length < 50) continue;
                                
                                // Create unique hash for this post (content + author)
                                var contentHash = cleanText.substring(0, 300) + '|' + profileLink + '|' + (name || '');
                                
                                // Skip duplicates
                                if (seenPosts.has(contentHash)) continue;
                                seenPosts.add(contentHash);
                                
                                // Get job links
                                var jobLinks = Array.prototype.slice.call(elem.querySelectorAll('a[href*="jobs/view"], a[href*="easyapply"]'));
                                var jobLink = jobLinks.length > 0 ? (jobLinks[0].href || jobLinks[0].getAttribute('href') || '') : '';
                                
                                // Get post link
                                var postLink = '';
                                // Try 1: Find link containing /feed/update/
                                var feedLink = elem.querySelector('a[href*="/feed/update/"]');
                                if (feedLink) {
                                    postLink = feedLink.href || feedLink.getAttribute('href') || '';
                                }
                                // Try 2: Find data-id or data-urn on elem or descendants
                                if (!postLink) {
                                    var urn = elem.getAttribute('data-id') || elem.getAttribute('data-urn') || '';
                                    if (!urn || urn.indexOf('urn:li:') < 0) {
                                        var urnElem = elem.querySelector('[data-id*="urn:li:"], [data-urn*="urn:li:"]');
                                        if (urnElem) {
                                            urn = urnElem.getAttribute('data-id') || urnElem.getAttribute('data-urn') || '';
                                        }
                                    }
                                    if (urn && urn.indexOf('urn:li:') >= 0) {
                                        var match = urn.match(/urn:li:(activity|share|ugcPost|update):\d+/);
                                        if (match) {
                                            postLink = 'https://www.linkedin.com/feed/update/' + match[0];
                                        }
                                    }
                                }
                                // Try 3: Find link containing /posts/
                                if (!postLink) {
                                    var postsLink = elem.querySelector('a[href*="/posts/"]');
                                    if (postsLink) {
                                        postLink = postsLink.href || postsLink.getAttribute('href') || '';
                                    }
                                }
                                // Try 4: Extract from replaceableCommentTools componentkey
                                if (!postLink) {
                                    var commentTools = elem.querySelector('[componentkey*="replaceableCommentTools"]');
                                    if (commentTools) {
                                        var compKey = commentTools.getAttribute('componentkey') || '';
                                        if (compKey) {
                                            try {
                                                var prefix = compKey.split('-')[0];
                                                while (prefix.length % 4 !== 0) {
                                                    prefix += '=';
                                                }
                                                var binary = atob(prefix.replace(/-/g, '+').replace(/_/g, '/'));
                                                var bytes = new Uint8Array(binary.length);
                                                for (var bIdx = 0; bIdx < binary.length; bIdx++) {
                                                    bytes[bIdx] = binary.charCodeAt(bIdx);
                                                }
                                                var val = 0n;
                                                var shift = 0n;
                                                for (var vIdx = 3; vIdx < bytes.length; vIdx++) {
                                                    var b = bytes[vIdx];
                                                    val |= BigInt(b & 0x7f) << shift;
                                                    if (!(b & 0x80)) break;
                                                    shift += 7n;
                                                }
                                                var activityId = val >> 1n;
                                                if (activityId > 0n) {
                                                    postLink = 'https://www.linkedin.com/feed/update/urn:li:activity:' + activityId.toString();
                                                }
                                            } catch (e) {
                                                // Ignore
                                            }
                                        }
                                    }
                                }
                                // Clean post link
                                if (postLink) {
                                    if (postLink.indexOf('?') > 0) {
                                        postLink = postLink.substring(0, postLink.indexOf('?'));
                                    }
                                    if (postLink.indexOf('#') > 0) {
                                        postLink = postLink.substring(0, postLink.indexOf('#'));
                                    }
                                    if (postLink.indexOf('http') < 0 && postLink.indexOf('/') === 0) {
                                        postLink = 'https://www.linkedin.com' + postLink;
                                    }
                                }

                                // Get images (exclude profile/avatar images)
                                var imgElements = Array.prototype.slice.call(elem.querySelectorAll('img[src*="media"], img[src*="licdn.com"]'));
                                var images = [];
                                for (var img = 0; img < imgElements.length; img++) {
                                    var imgSrc = imgElements[img].src || imgElements[img].getAttribute('data-delayed-url') || '';
                                    if (imgSrc && imgSrc.indexOf('media') >= 0 && 
                                        imgSrc.indexOf('profile') < 0 && imgSrc.indexOf('avatar') < 0) {
                                        images.push(imgSrc);
                                        if (images.length >= 5) break;
                                    }
                                }
                                
                                // Extract comments
                                var comments = [];
                                try {
                                    var commentBtn = elem.querySelector('button[aria-label*="Comment"]');
                                    if (commentBtn) {
                                        var btnText = (commentBtn.innerText || '').trim();
                                        if (btnText && /^\d+$/.test(btnText) && parseInt(btnText) > 0) {
                                            commentBtn.click();
                                            await new Promise(function(resolve) { setTimeout(resolve, 1500); });
                                            
                                            // Find all containers and filter out nested ones
                                            var allContainers = elem.querySelectorAll('[componentkey*="urn:li:comment:"]');
                                            var commentContainers = [];
                                            for (var cIdx = 0; cIdx < allContainers.length; cIdx++) {
                                                var c = allContainers[cIdx];
                                                var parent = c.parentElement;
                                                var isNested = false;
                                                while (parent && parent !== elem) {
                                                    var pKey = parent.getAttribute('componentkey') || '';
                                                    if (pKey && pKey.indexOf('urn:li:comment:') >= 0) {
                                                        isNested = true;
                                                        break;
                                                    }
                                                    parent = parent.parentElement;
                                                }
                                                if (!isNested) {
                                                    commentContainers.push(c);
                                                }
                                            }
                                            
                                            for (var cIdx = 0; cIdx < commentContainers.length; cIdx++) {
                                                var cContainer = commentContainers[cIdx];
                                                var commenterName = '';
                                                var commenterProfile = '';
                                                
                                                var allLinks = cContainer.querySelectorAll('a[href*="/in/"], a[href*="/company/"]');
                                                for (var lIdx = 0; lIdx < allLinks.length; lIdx++) {
                                                    var link = allLinks[lIdx];
                                                    var nameElem = link.querySelector('[aria-hidden="true"]');
                                                    var rawName = '';
                                                    if (nameElem) {
                                                        rawName = (nameElem.innerText || '').trim();
                                                    } else {
                                                        rawName = (link.innerText || '').trim();
                                                    }
                                                    if (rawName) {
                                                        // Clean the name using our robust split chain
                                                        commenterName = rawName.split('\\n')[0].split('•')[0].split('·')[0].split('Author')[0].split(',')[0].trim();
                                                        commenterProfile = link.href || link.getAttribute('href') || '';
                                                        if (commenterProfile) {
                                                            if (commenterProfile.indexOf('?') > 0) {
                                                                commenterProfile = commenterProfile.substring(0, commenterProfile.indexOf('?'));
                                                            }
                                                            if (commenterProfile.indexOf('http') < 0 && commenterProfile.indexOf('/') === 0) {
                                                                commenterProfile = 'https://www.linkedin.com' + commenterProfile;
                                                            }
                                                        }
                                                        break;
                                                    }
                                                }
                                                
                                                var commentText = '';
                                                var textBoxes = cContainer.querySelectorAll('[data-testid="expandable-text-box"]');
                                                if (textBoxes && textBoxes.length > 0) {
                                                    var lastBox = textBoxes[textBoxes.length - 1];
                                                    var moreBtn = lastBox.querySelector('button');
                                                    var cleanText = (lastBox.innerText || '').trim();
                                                    if (moreBtn) {
                                                        var moreText = (moreBtn.innerText || '').trim();
                                                        if (cleanText.endsWith(moreText)) {
                                                            cleanText = cleanText.substring(0, cleanText.length - moreText.length).trim();
                                                        }
                                                        if (cleanText.endsWith('…')) {
                                                            cleanText = cleanText.substring(0, cleanText.length - 1).trim();
                                                        }
                                                    }
                                                    commentText = cleanText.replace(/\\s+/g, ' ').trim();
                                                }
                                                
                                                if (commenterName && commentText) {
                                                    comments.push({
                                                        commenter_name: commenterName,
                                                        commenter_profile_link: commenterProfile,
                                                        comment_text: commentText
                                                    });
                                                }
                                            }
                                        }
                                    }
                                } catch (commentErr) {
                                    // Ignore
                                }
                                
                                // Only add if we have valid data
                                if (cleanText.length >= 50 && profileLink && profileLink.indexOf('/in/') >= 0) {
                                    posts.push({
                                        text: cleanText.substring(0, 5000),
                                        name: name || '',
                                        profile_link: profileLink,
                                        job_application_link: jobLink,
                                        post_link: postLink,
                                        image_links: images,
                                        comments: comments
                                    });
                                }
                            } catch (e) {
                                // Skip this element if there's an error
                                continue;
                            }
                        }
                        
                        return posts;
                    })();
                """)
                
                print(f"\n{'='*60}", flush=True)
                print(f"JAVASCRIPT EXTRACTION RESULTS", flush=True)
                print(f"{'='*60}", flush=True)
                print(f"Posts found: {len(js_posts) if js_posts else 0} (type: {type(js_posts)})", flush=True)
                
                if js_posts and len(js_posts) > 0:
                    print(f"✓ JavaScript extraction found {len(js_posts)} posts!", flush=True)
                    
                    # DIAGNOSTIC: Show breakdown of posts
                    posts_with_name = sum(1 for p in js_posts if p.get('name'))
                    posts_with_profile = sum(1 for p in js_posts if p.get('profile_link'))
                    posts_with_text = sum(1 for p in js_posts if p.get('text') and len(p.get('text', '')) > 50)
                    
                    print(f"DIAGNOSTIC BREAKDOWN:", flush=True)
                    print(f"  Posts with name: {posts_with_name}/{len(js_posts)}", flush=True)
                    print(f"  Posts with profile_link: {posts_with_profile}/{len(js_posts)}", flush=True)
                    print(f"  Posts with substantial text (>50 chars): {posts_with_text}/{len(js_posts)}", flush=True)
                    
                    # Log first few posts for debugging
                    print(f"\nSAMPLE POSTS (first 3):", flush=True)
                    for i, post in enumerate(js_posts[:3]):
                        text_preview = post.get('text', '')[:100] if post.get('text') else 'No text'
                        name = post.get('name', 'N/A')
                        profile = post.get('profile_link', 'N/A')
                        print(f"  Post {i+1}:", flush=True)
                        print(f"    Name: {name}", flush=True)
                        print(f"    Profile: {profile[:80] if profile != 'N/A' else 'N/A'}", flush=True)
                        print(f"    Text preview: {text_preview}...", flush=True)
                    print(f"{'='*60}\n", flush=True)
                    # Convert JavaScript results to our format
                    extracted_posts = []
                    for js_post in js_posts:
                        if js_post.get('text') or js_post.get('name'):
                            extracted_posts.append({
                                'text': js_post.get('text', ''),
                                'name': js_post.get('name', ''),
                                'profile_link': js_post.get('profile_link', ''),
                                'job_application_link': js_post.get('job_application_link', ''),
                                'post_link': js_post.get('post_link', ''),
                                'image_links': js_post.get('image_links', []),
                                'comments': js_post.get('comments', [])
                            })
                    
                    if extracted_posts:
                        print(f"Successfully extracted {len(extracted_posts)} posts using JavaScript!", flush=True)
                        return extracted_posts
                else:
                    print("JavaScript extraction found 0 posts", flush=True)
            except Exception as js_error:
                print(f"JavaScript extraction failed: {str(js_error)}", flush=True)
                import traceback
                print(f"Traceback: {traceback.format_exc()}", flush=True)
            
            return []
        
        print(f"Processing {len(post_elements)} post elements...", flush=True)
        
        seen_texts = set()  # Avoid duplicates
        
        for idx, post_element in enumerate(post_elements):
            try:
                post_data = self._extract_single_post(post_element, page)
                if post_data and post_data.get('text'):
                    # Check for duplicates - use more comprehensive hash
                    # Include name and profile link to distinguish similar posts from different authors
                    name_part = post_data.get('name', '')[:50] if post_data.get('name') else ''
                    profile_part = post_data.get('profile_link', '')[:50] if post_data.get('profile_link') else ''
                    first_words = ' '.join(post_data['text'].split()[:10])[:100] if post_data.get('text') else ''
                    text_hash = hash(post_data['text'][:500] + str(len(post_data['text'])) + name_part + profile_part + first_words)
                    if text_hash not in seen_texts:
                        seen_texts.add(text_hash)
                        posts.append(post_data)
                        print(f"Extracted post {len(posts)}: {post_data.get('name', 'Unknown')}", flush=True)
            except Exception as e:
                print(f"Error extracting post {idx+1}: {str(e)}", flush=True)
                continue
        
        # #region agent log
        try:
            with open(log_path, 'a') as log_file:
                log_file.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H1",
                    "location": "linkedin_scraper.py:_extract_posts",
                    "message": "Post extraction completed",
                    "data": {"posts_found": len(posts), "elements_processed": len(post_elements)},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except: pass
        # #endregion
        
        return posts
    
    def _extract_single_post(self, post_element, page: Page) -> Optional[Dict]:
        """
        Extract data from a single post element.
        
        Args:
            post_element: Playwright element handle
            page: Playwright page object
            
        Returns:
            Dictionary with post data or None
        """
        post_data = {
            'text': '',
            'name': '',
            'profile_link': '',
            'job_application_link': '',
            'post_link': '',
            'image_links': []
        }
        
        try:
            # Extract post text - try multiple strategies
            text_selectors = [
                'div[data-test-id="main-feed-activity-card__commentary"]',
                'div.feed-shared-text',
                'span[class*="feed-shared-text"]',
                'div[class*="update-components-text"]',
                'span[dir="ltr"]',
                'div[class*="feed-shared-update-v2__description"]',
                'div[class*="feed-shared-text-view"]'
            ]
            
            for selector in text_selectors:
                try:
                    text_elem = post_element.query_selector(selector)
                    if text_elem:
                        text = text_elem.inner_text().strip()
                        if text and len(text) > 10:  # Only use if substantial text
                            post_data['text'] = text
                            break
                except:
                    continue
            
            # If no text found with selectors, try getting all text and filtering
            if not post_data['text']:
                try:
                    all_text = post_element.inner_text()
                    # Filter out very short or likely non-post text
                    if all_text and len(all_text) > 20:
                        post_data['text'] = all_text[:500]  # Limit to first 500 chars
                except:
                    pass
            
            # Extract poster name
            # Based on LinkedIn's current structure: name is in update-components-actor__title
            name_selectors = [
                'span.update-components-actor__title span[dir="ltr"]',  # Most specific - matches the HTML structure
                'span.update-components-actor__title',  # Fallback to title span
                'a.update-components-actor__meta-link span.update-components-actor__title',  # Via meta link
                'span[class*="update-components-actor__title"]',  # Class contains
                'span[class*="feed-shared-actor__name"]',
                'a[class*="feed-shared-actor__name-link"]',
                'span[class*="update-components-actor__name"]',
                'a[data-control-name="actor_container"] span',
                'span[class*="actor-name"]',
                'a[class*="actor-name"]'
            ]
            
            for selector in name_selectors:
                try:
                    name_elem = post_element.query_selector(selector)
                    if name_elem:
                        name = name_elem.inner_text().strip()
                        # Clean up the name - remove extra whitespace and hidden text artifacts
                        if name:
                            # Sometimes LinkedIn has hidden text, try to get visible text only
                            # Check if there's a span with aria-hidden="true" that has the actual name
                            try:
                                visible_name_elem = name_elem.query_selector('span[aria-hidden="true"]')
                                if visible_name_elem:
                                    visible_name = visible_name_elem.inner_text().strip()
                                    if visible_name and len(visible_name) > 0:
                                        name = visible_name
                            except:
                                pass
                            
                            # Filter out very short or non-name text
                            if name and len(name) > 1 and len(name) < 100:  # Names are usually 1-100 chars
                                # Remove common non-name patterns
                                if not name.lower().startswith(('view', 'follow', '•', 'ago', 'minute', 'hour', 'day')):
                                    post_data['name'] = name
                                    break
                except:
                    continue
            
            # If still no name found, try getting text from the actor container link's aria-label
            if not post_data['name']:
                try:
                    actor_link = post_element.query_selector('a.update-components-actor__meta-link')
                    if actor_link:
                        aria_label = actor_link.get_attribute('aria-label')
                        if aria_label:
                            # aria-label format: "View: Sirazul Haque 3rd+ ..."
                            # Extract name part (usually after "View: " and before connection info)
                            if 'View:' in aria_label:
                                name_part = aria_label.split('View:')[1].strip()
                                # Remove connection info (like "3rd+", "2nd", etc.)
                                name_part = name_part.split('•')[0].strip() if '•' in name_part else name_part
                                name_part = name_part.split('1st')[0].strip() if '1st' in name_part else name_part
                                name_part = name_part.split('2nd')[0].strip() if '2nd' in name_part else name_part
                                name_part = name_part.split('3rd')[0].strip() if '3rd' in name_part else name_part
                                if name_part and len(name_part) > 1 and len(name_part) < 100:
                                    post_data['name'] = name_part
                except:
                    pass
            
            # Extract profile link
            profile_link_selectors = [
                'a.update-components-actor__meta-link',  # Most specific - matches current LinkedIn structure
                'a[class*="update-components-actor__meta-link"]',  # Class contains
                'a.update-components-actor__image',  # Profile image link
                'a[class*="feed-shared-actor__name-link"]',
                'a[data-control-name="actor_container"]',
                'a[class*="update-components-actor__container"]',
                'a[href*="/in/"]',
                'a[href*="/company/"]'
            ]
            
            for selector in profile_link_selectors:
                try:
                    link_elem = post_element.query_selector(selector)
                    if link_elem:
                        href = link_elem.get_attribute('href')
                        if href and ('/in/' in href or '/company/' in href):
                            # Clean up the URL - remove query params and fragments
                            if href.startswith('/'):
                                post_data['profile_link'] = f"https://www.linkedin.com{href.split('?')[0].split('#')[0]}"
                            else:
                                post_data['profile_link'] = href.split('?')[0].split('#')[0]  # Remove query params and fragments
                            break
                except:
                    continue
            
            # Extract job application links
            # Look for links that might be job applications
            try:
                all_links = post_element.query_selector_all('a[href*="jobs"]')
                for link in all_links:
                    try:
                        href = link.get_attribute('href')
                        link_text = link.inner_text().lower()
                        if href and ('apply' in href.lower() or 'jobs/view' in href.lower() or 
                                    'apply' in link_text or 'job' in link_text):
                            if href.startswith('/'):
                                post_data['job_application_link'] = f"https://www.linkedin.com{href.split('?')[0]}"
                            else:
                                post_data['job_application_link'] = href.split('?')[0]
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract image links
            image_selectors = [
                'img[class*="feed-shared-image"]',
                'img[class*="update-components-image"]',
                'img[data-delayed-url]',
                'img[src*="media"]',
                'img[src*="licdn.com"]'
            ]
            
            for selector in image_selectors:
                try:
                    img_elements = post_element.query_selector_all(selector)
                    for img in img_elements:
                        img_url = img.get_attribute('src') or img.get_attribute('data-delayed-url') or img.get_attribute('data-src')
                        if img_url and 'media' in img_url and img_url not in post_data['image_links']:
                            # Filter out small icons/avatars - only include if NOT a profile/avatar image
                            if 'profile' not in img_url.lower() and 'avatar' not in img_url.lower():
                                post_data['image_links'].append(img_url)
                except:
                    continue
            
            # Extract post link
            post_link = ''
            # Try 1: Find link containing /feed/update/
            try:
                feed_link_elem = post_element.query_selector('a[href*="/feed/update/"]')
                if feed_link_elem:
                    href = feed_link_elem.get_attribute('href')
                    if href:
                        if href.startswith('/'):
                            post_link = f"https://www.linkedin.com{href.split('?')[0].split('#')[0]}"
                        else:
                            post_link = href.split('?')[0].split('#')[0]
            except:
                pass
                
            # Try 2: Find data-id or data-urn on element itself or descendants
            if not post_link:
                try:
                    urn = None
                    for attr in ['data-id', 'data-urn']:
                        val = post_element.get_attribute(attr)
                        if val and 'urn:li:' in val:
                            urn = val
                            break
                        desc = post_element.query_selector(f'[{attr}*="urn:li:"]')
                        if desc:
                            val = desc.get_attribute(attr)
                            if val and 'urn:li:' in val:
                                urn = val
                                break
                    if urn:
                        import re
                        match = re.search(r'urn:li:(activity|share|ugcPost|update):\d+', urn)
                        if match:
                            post_link = f"https://www.linkedin.com/feed/update/{match.group(0)}"
                except:
                    pass
                    
            # Try 3: Find link containing /posts/
            if not post_link:
                try:
                    posts_link_elem = post_element.query_selector('a[href*="/posts/"]')
                    if posts_link_elem:
                        href = posts_link_elem.get_attribute('href')
                        if href:
                            if href.startswith('/'):
                                post_link = f"https://www.linkedin.com{href.split('?')[0].split('#')[0]}"
                            else:
                                post_link = href.split('?')[0].split('#')[0]
                except:
                    pass
                    
            # Try 4: Extract from replaceableCommentTools componentkey
            if not post_link:
                try:
                    comment_tools = post_element.query_selector('[componentkey*="replaceableCommentTools"]')
                    if comment_tools:
                        comp_key = comment_tools.get_attribute('componentkey')
                        if comp_key:
                            prefix = comp_key.split('-')[0]
                            import base64
                            padded = prefix + "=" * ((4 - len(prefix) % 4) % 4)
                            decoded_bytes = base64.b64decode(padded)
                            varint_bytes = decoded_bytes[3:]
                            val = 0
                            shift = 0
                            for b in varint_bytes:
                                val |= (b & 0x7f) << shift
                                if not (b & 0x80):
                                    break
                                shift += 7
                            activity_id = val >> 1
                            if activity_id > 0:
                                post_link = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}"
                except:
                    pass
                    
            post_data['post_link'] = post_link
            
            # Extract comments
            comments = []
            try:
                comment_btn = post_element.query_selector('button[aria-label*="Comment"]')
                if comment_btn:
                    btn_text = comment_btn.inner_text().strip()
                    if btn_text and btn_text.isdigit() and int(btn_text) > 0:
                        comment_btn.click()
                        page.wait_for_timeout(1500)
                        
                        # Find all containers and filter out nested ones
                        all_containers = post_element.query_selector_all('[componentkey*="urn:li:comment:"]')
                        comment_containers = []
                        for c in all_containers:
                            parent = c.query_selector('xpath=..')
                            is_nested = False
                            while parent and parent != post_element:
                                try:
                                    p_key = parent.get_attribute('componentkey') or ''
                                    if p_key and 'urn:li:comment:' in p_key:
                                        is_nested = True
                                        break
                                except:
                                    pass
                                parent = parent.query_selector('xpath=..')
                            if not is_nested:
                                comment_containers.append(c)
                        
                        for c_container in comment_containers:
                            commenter_name = ''
                            commenter_profile = ''
                            
                            all_links = c_container.query_selector_all('a[href*="/in/"], a[href*="/company/"]')
                            for link in all_links:
                                name_elem = link.query_selector('[aria-hidden="true"]')
                                if name_elem:
                                    raw_name = name_elem.inner_text().strip()
                                else:
                                    raw_name = link.inner_text().strip()
                                    
                                if raw_name:
                                    import re
                                    commenter_name = re.split(r'\n|•|·|Author|,', raw_name)[0].strip()
                                    commenter_profile = link.get_attribute('href') or ''
                                    if commenter_profile:
                                        if '?' in commenter_profile:
                                            commenter_profile = commenter_profile.split('?')[0]
                                        if not commenter_profile.startswith('http') and commenter_profile.startswith('/'):
                                            commenter_profile = f"https://www.linkedin.com{commenter_profile}"
                                    break
                                    
                            comment_text = ''
                            text_boxes = c_container.query_selector_all('[data-testid="expandable-text-box"]')
                            if text_boxes:
                                last_box = text_boxes[-1]
                                more_btn = last_box.query_selector('button')
                                clean_text = last_box.inner_text().strip()
                                if more_btn:
                                    more_text = more_btn.inner_text().strip()
                                    if clean_text.endswith(more_text):
                                        clean_text = clean_text[:-len(more_text)].strip()
                                    if clean_text.endswith('…'):
                                        clean_text = clean_text[:-1].strip()
                                import re
                                comment_text = re.sub(r'\s+', ' ', clean_text).strip()
                                
                            if commenter_name and comment_text:
                                comments.append({
                                    'commenter_name': commenter_name,
                                    'commenter_profile_link': commenter_profile,
                                    'comment_text': comment_text
                                })
            except Exception as e:
                # Ignore comment errors
                pass
                
            post_data['comments'] = comments
            
            # Only return if we have at least text or name
            if post_data['text'] or post_data['name']:
                return post_data
            else:
                return None
            
        except Exception as e:
            print(f"Error in _extract_single_post: {str(e)}")
            return None
    
    def save_to_json(self, filename: str = 'linkedin_posts.json'):
        """
        Save scraped posts to a JSON file.
        
        Args:
            filename: Output JSON filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.posts_data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.posts_data)} posts to {filename}")


def main():
    """Main function to run the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Post Scraper')
    parser.add_argument('url', help='LinkedIn search results URL')
    parser.add_argument('--cookies', '-c', help='Path to JSON file containing cookies')
    parser.add_argument('--output', '-o', default='linkedin_posts.json', help='Output JSON filename')
    parser.add_argument('--scrolls', '-s', type=int, default=5, help='Number of scrolls to load more posts')
    parser.add_argument('--scroll-delay', '-d', type=int, default=2, help='Delay between scrolls in seconds')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode (default: visible window)')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = LinkedInScraper()
    
    # Load cookies if provided
    if args.cookies:
        scraper.load_cookies_from_file(args.cookies)
    
    # Scrape posts (default: non-headless mode to avoid detection)
    # Uses Firefox by default for better macOS compatibility in non-headless mode
    posts = scraper.scrape_posts(args.url, max_scroll=args.scrolls, scroll_delay=args.scroll_delay, headless=args.headless)
    scraper.posts_data = posts
    
    # Save to JSON
    scraper.save_to_json(args.output)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Scraping completed!")
    print(f"Total posts scraped: {len(posts)}")
    print(f"Output saved to: {args.output}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()


