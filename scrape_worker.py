#!/usr/bin/env python3
"""
Standalone worker script for scraping LinkedIn posts.
This script is called as a subprocess to avoid Playwright issues with ProcessPoolExecutor.
"""

import sys
import json
import os

# Set environment variables before importing Playwright
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.expanduser('~/.cache/ms-playwright')
os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '0'
os.environ['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = '1'

# Redirect stdout to stderr for all debug output
# This ensures only JSON goes to stdout for the API to parse
# We'll restore stdout just before printing the final JSON result
original_stdout = sys.stdout
sys.stdout = sys.stderr

from linkedin_scraper import LinkedInScraper

def main():
    """Main function that runs scraping and outputs JSON result."""
    if len(sys.argv) < 2:
        error_result = {
            "success": False,
            "error": "Missing arguments",
            "posts": [],
            "count": 0
        }
        print(json.dumps(error_result), flush=True)
        sys.exit(1)
    
    try:
        # Parse arguments from JSON
        args = json.loads(sys.argv[1])
        action = args.get('action', 'scrape_posts')
        cookies_file = args['cookies_file']
        url = args['url']
        max_scroll = args.get('max_scroll', 5)
        scroll_delay = args.get('scroll_delay', 2)
        headless = args.get('headless', True)
        proxy = args.get('proxy', None)
        max_comments = args.get('max_comments', 50)
        
        # Load cookies
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
        
        # Create scraper
        scraper = LinkedInScraper(cookies=cookies)
        
        if action == 'scrape_comments':
            comments = scraper.scrape_comments(
                post_url=url,
                max_comments=max_comments,
                headless=headless
            )
            # Restore stdout and output result as JSON
            sys.stdout = original_stdout
            result = {
                "success": True,
                "comments": comments,
                "count": len(comments) if comments else 0
            }
            print(json.dumps(result), flush=True)
            sys.exit(0)
        else:
            posts = scraper.scrape_posts(
                url=url,
                max_scroll=max_scroll,
                scroll_delay=scroll_delay,
                headless=headless,
                proxy=proxy
            )
            # Restore stdout and output result as JSON
            sys.stdout = original_stdout
            result = {
                "success": True,
                "posts": posts,
                "count": len(posts) if posts else 0
            }
            print(json.dumps(result), flush=True)
            sys.exit(0)
        
    except Exception as e:
        # Restore stdout and output JSON error result
        sys.stdout = original_stdout
        error_result = {
            "success": False,
            "error": str(e),
            "posts": [],
            "count": 0
        }
        print(json.dumps(error_result), flush=True)
        # Print traceback to stderr for debugging
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

