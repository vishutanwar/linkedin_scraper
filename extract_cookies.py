#!/usr/bin/env python3
"""
Helper script to extract cookies from browser.
This provides instructions for manual cookie extraction.
"""

import json
import sys


def print_instructions():
    """Print instructions for extracting cookies."""
    print("=" * 70)
    print("LinkedIn Cookie Extraction Guide")
    print("=" * 70)
    print("\nMethod 1: Using Browser Extension (Recommended)")
    print("-" * 70)
    print("1. Install 'Cookie Editor' extension for Chrome/Edge/Firefox")
    print("2. Go to https://www.linkedin.com and log in")
    print("3. Click the Cookie Editor extension icon")
    print("4. Click 'Export' → 'Export as JSON'")
    print("5. Save the file as 'linkedin_cookies.json'")
    print("\nMethod 2: Manual Extraction")
    print("-" * 70)
    print("1. Log in to LinkedIn in your browser")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Application tab (Chrome) or Storage tab (Firefox)")
    print("4. Navigate to Cookies → https://www.linkedin.com")
    print("5. Copy the following important cookies:")
    print("   - li_at (most important for authentication)")
    print("   - JSESSIONID")
    print("   - bcookie")
    print("   - bscookie")
    print("   - lang")
    print("6. Create a JSON file with this format:")
    print("\nExample cookie format:")
    print("-" * 70)
    
    example_cookies = [
        {
            "name": "li_at",
            "value": "YOUR_LI_AT_VALUE_HERE",
            "domain": ".linkedin.com",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        },
        {
            "name": "JSESSIONID",
            "value": "YOUR_JSESSIONID_VALUE_HERE",
            "domain": ".linkedin.com",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        }
    ]
    
    print(json.dumps(example_cookies, indent=2))
    print("\n" + "=" * 70)
    print("\nAfter extracting cookies, save them to a file (e.g., linkedin_cookies.json)")
    print("Then use the scraper with: python linkedin_scraper.py <URL> --cookies linkedin_cookies.json")
    print("=" * 70)


def create_template():
    """Create a template cookie file."""
    template = [
        {
            "name": "li_at",
            "value": "REPLACE_WITH_YOUR_COOKIE_VALUE",
            "domain": ".linkedin.com",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        },
        {
            "name": "JSESSIONID",
            "value": "REPLACE_WITH_YOUR_COOKIE_VALUE",
            "domain": ".linkedin.com",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        },
        {
            "name": "bcookie",
            "value": "REPLACE_WITH_YOUR_COOKIE_VALUE",
            "domain": ".linkedin.com",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": True,
            "sameSite": "None"
        },
        {
            "name": "bscookie",
            "value": "REPLACE_WITH_YOUR_COOKIE_VALUE",
            "domain": ".linkedin.com",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": True,
            "sameSite": "None"
        }
    ]
    
    filename = "linkedin_cookies_template.json"
    with open(filename, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"\nTemplate created: {filename}")
    print("Fill in the cookie values and rename to linkedin_cookies.json")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--create-template':
        create_template()
    else:
        print_instructions()
        print("\nTo create a template file, run: python extract_cookies.py --create-template")

