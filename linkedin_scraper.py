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
    
    def scrape_posts(self, url: str, max_scroll: int = 5, scroll_delay: int = 2, headless: bool = False) -> List[Dict]:
        """
        Scrape LinkedIn posts from the given URL.
        
        Args:
            url: LinkedIn search results URL
            max_scroll: Maximum number of scrolls to load more posts
            scroll_delay: Delay between scrolls in seconds
            headless: Run browser in headless mode (default: False)
            
        Returns:
            List of dictionaries containing post data
        """
        with sync_playwright() as p:
            # Try Firefox first for non-headless mode (more stable on macOS)
            # Fallback to Chromium if Firefox fails
            browser = None
            browser_type = None
            
            # Try Firefox first (better for non-headless on macOS)
            firefox_launched = False
            if not headless:
                try:
                    print(f"Attempting to launch Firefox browser (headless={headless})...")
                    browser = p.firefox.launch(headless=headless)
                    browser_type = 'firefox'
                    firefox_launched = True
                    print("Firefox browser launched successfully")
                except Exception as firefox_error:
                    print(f"Firefox launch failed: {str(firefox_error)}")
                    print("Trying Chromium...")
            
            # Try Chromium if Firefox failed or if headless mode
            if not browser:
                try:
                    print(f"Attempting to launch Chromium browser (headless={headless})...")
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
                    
                    browser = p.chromium.launch(**launch_args)
                    browser_type = 'chromium'
                    print("Chromium browser launched successfully")
                except Exception as chromium_error:
                    print(f"Chromium launch failed: {str(chromium_error)}")
                    # If Firefox also failed and we're in non-headless, try Firefox again
                    if not headless:
                        print("Retrying Firefox...")
                        try:
                            browser = p.firefox.launch(headless=headless)
                            browser_type = 'firefox'
                            print("Firefox browser launched successfully on retry")
                        except:
                            pass
                    
                    # Last resort: WebKit
                    if not browser:
                        print("Trying WebKit as last resort...")
                        try:
                            browser = p.webkit.launch(headless=headless)
                            browser_type = 'webkit'
                            print("WebKit browser launched successfully")
                        except Exception as webkit_error:
                            print(f"All browsers failed to launch!")
                            if 'chromium_error' in locals():
                                print(f"Chromium error: {str(chromium_error)}")
                            if 'firefox_error' in locals():
                                print(f"Firefox error: {str(firefox_error)}")
                            print(f"WebKit error: {str(webkit_error)}")
                            raise Exception("Could not launch any browser. Please check Playwright installation.")
            
            if not browser:
                raise Exception("Browser launch failed")
            
            try:
                # Create browser context
                print("Creating browser context...")
                # Set appropriate user agent based on browser type
                if browser_type == 'firefox':
                    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0'
                else:
                    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=True
                )
                print("Browser context created")
                
                # Create page
                print("Creating page...")
                page = context.new_page()
                print("Page created successfully")
                
                # Navigate to LinkedIn domain first before adding cookies
                # This ensures the browser context is properly initialized
                print("Initializing browser context by navigating to LinkedIn...")
                try:
                    page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=30000)
                    print("Successfully navigated to LinkedIn")
                    time.sleep(2)  # Wait for page to initialize
                except Exception as nav_error:
                    print(f"Warning during initial navigation: {str(nav_error)}")
                    print("Continuing anyway...")
                
                # Add cookies if provided (after navigating to domain)
                if self.cookies:
                    try:
                        print(f"Adding {len(self.cookies)} cookies...")
                        context.add_cookies(self.cookies)
                        print(f"Successfully added {len(self.cookies)} cookies to browser context")
                        # Reload page to apply cookies
                        page.reload(wait_until='domcontentloaded', timeout=30000)
                        time.sleep(2)
                    except Exception as cookie_error:
                        print(f"Warning: Error adding cookies: {str(cookie_error)}")
                        print("Continuing without cookies...")
                
                # Now navigate to the actual target URL
                print(f"Navigating to target URL: {url}")
                navigation_success = False
                try:
                    # Use 'domcontentloaded' instead of 'networkidle' - LinkedIn has continuous network activity
                    page.goto(url, wait_until='domcontentloaded', timeout=60000)
                    print("Successfully navigated to target URL")
                    navigation_success = True
                except Exception as nav_error:
                    print(f"Navigation timeout or error: {str(nav_error)}")
                    print("Page may still be loading. Checking current URL...")
                    try:
                        current_url = page.url
                        print(f"Current URL: {current_url}")
                        # If we're on LinkedIn domain, continue anyway
                        if 'linkedin.com' in current_url:
                            print("On LinkedIn domain. Continuing with scraping...")
                            navigation_success = True
                        else:
                            print("Not on LinkedIn domain. Waiting 5 seconds and retrying...")
                            time.sleep(5)
                            try:
                                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                                navigation_success = True
                            except:
                                print("Retry failed. Continuing anyway...")
                                navigation_success = True  # Continue to try scrolling
                    except:
                        print("Could not check URL. Continuing anyway...")
                        navigation_success = True  # Continue to try scrolling
                
                # Check for account selection/login page and handle it
                print("Checking for account selection/login page...")
                self._handle_account_selection(page)
                
                # Wait for page to settle
                print("Waiting for page content to load...")
                time.sleep(5)
                
                # Check if page has content before scrolling
                try:
                    page_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
                    print(f"Initial page height: {page_height}px")
                    if page_height < 500:
                        print("Page height is very small. Waiting more for content to load...")
                        time.sleep(5)
                        page_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
                        print(f"Page height after wait: {page_height}px")
                except Exception as e:
                    print(f"Could not check page height: {str(e)}")
                
                # Scroll to load more posts
                print(f"\nScrolling to load more posts (max {max_scroll} times)...")
                last_height = 0
                no_change_count = 0
                
                for i in range(max_scroll):
                    try:
                        # Get current page height
                        current_height = page.evaluate("""
                            () => {
                                return Math.max(
                                    document.body.scrollHeight,
                                    document.documentElement.scrollHeight,
                                    document.body.offsetHeight,
                                    document.documentElement.offsetHeight
                                );
                            }
                        """)
                        
                        # Scroll down
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight || document.documentElement.scrollHeight)")
                        time.sleep(scroll_delay)
                        
                        # Check if new content loaded
                        new_height = page.evaluate("""
                            () => {
                                return Math.max(
                                    document.body.scrollHeight,
                                    document.documentElement.scrollHeight,
                                    document.body.offsetHeight,
                                    document.documentElement.offsetHeight
                                );
                            }
                        """)
                        
                        if new_height == current_height:
                            no_change_count += 1
                            if no_change_count >= 3:
                                print(f"No new content loaded after {no_change_count} scrolls. Stopping scroll.")
                                break
                        else:
                            no_change_count = 0  # Reset if content loaded
                        
                        print(f"Scroll {i+1}/{max_scroll} completed (page height: {new_height}px)")
                        last_height = new_height
                        
                    except Exception as scroll_error:
                        print(f"Error during scroll {i+1}: {str(scroll_error)}")
                        # Try to continue scrolling
                        try:
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight || document.documentElement.scrollHeight)")
                            time.sleep(scroll_delay)
                        except:
                            print("Could not continue scrolling. Stopping.")
                            break
                
                # Extract posts
                print("Extracting posts...")
                posts = self._extract_posts(page)
                print(f"Found {len(posts)} posts")
                
                return posts
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
            finally:
                try:
                    if 'browser' in locals() and browser:
                        browser.close()
                        print("Browser closed")
                except:
                    pass
    
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
            
            # Check if we're on account selection/login page
            is_account_selection = (
                'checkpoint' in current_url.lower() or
                'login' in current_url.lower() or
                'login' in page_title or
                'sign in' in page_title or
                'welcome back' in page_title
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
        posts = []
        
        # Wait for content to load
        try:
            page.wait_for_selector('body', timeout=10000)
        except:
            pass
        
        # LinkedIn post containers - these selectors may need adjustment based on LinkedIn's current structure
        # Try multiple selectors to find posts
        post_selectors = [
            'div[data-id*="urn:li:activity"]',
            'div.feed-shared-update-v2',
            'div[class*="feed-shared-update-v2"]',
            'article[data-id]',
            'div[class*="update-components"]',
            'div[class*="feed-shared-update-v2__description"]',
            'div[data-urn*="urn:li:activity"]'
        ]
        
        post_elements = []
        for selector in post_selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    post_elements = elements
                    print(f"Found {len(elements)} posts using selector: {selector}")
                    break
            except:
                continue
        
        if not post_elements:
            # Fallback: try to find any post-like elements by looking for common patterns
            fallback_selectors = [
                'div[class*="feed"]',
                'article',
                'div[role="article"]'
            ]
            for selector in fallback_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements and len(elements) > 5:  # Likely posts if we find many
                        post_elements = elements
                        print(f"Using fallback selector: {selector}, found {len(elements)} elements")
                        break
                except:
                    continue
        
        if not post_elements:
            print("Warning: No posts found. The page structure may have changed or you may not be logged in.")
            # Try to save page HTML for debugging
            try:
                html_content = page.content()
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print("Page HTML saved to debug_page.html for inspection")
            except:
                pass
            return []
        
        print(f"Processing {len(post_elements)} post elements...")
        
        seen_texts = set()  # Avoid duplicates
        
        for idx, post_element in enumerate(post_elements):
            try:
                post_data = self._extract_single_post(post_element, page)
                if post_data and post_data.get('text'):
                    # Check for duplicates
                    text_hash = hash(post_data['text'][:100])  # Use first 100 chars as identifier
                    if text_hash not in seen_texts:
                        seen_texts.add(text_hash)
                        posts.append(post_data)
                        print(f"Extracted post {len(posts)}: {post_data.get('name', 'Unknown')}")
            except Exception as e:
                print(f"Error extracting post {idx+1}: {str(e)}")
                continue
        
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

