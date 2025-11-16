#!/usr/bin/env python3
"""
Example usage of the LinkedIn scraper programmatically.
"""

from linkedin_scraper import LinkedInScraper

# Example 1: Using cookies from file
def example_with_cookie_file():
    """Example using cookies from a JSON file."""
    scraper = LinkedInScraper()
    scraper.load_cookies_from_file('linkedin_cookies.json')
    
    url = "https://www.linkedin.com/search/results/content/?datePosted=%22past-24h%22&keywords=(%23n8n%20AND%20(%23hiring%20OR%20hiring))%20OR%20(%22workflow%20automations%22)&origin=GLOBAL_SEARCH_HEADER&sid=p2E"
    
    posts = scraper.scrape_posts(url, max_scroll=5, scroll_delay=2, headless=False)
    scraper.posts_data = posts
    scraper.save_to_json('output.json')
    
    print(f"Scraped {len(posts)} posts")
    for i, post in enumerate(posts[:3], 1):  # Show first 3 posts
        print(f"\nPost {i}:")
        print(f"  Name: {post.get('name', 'N/A')}")
        print(f"  Text: {post.get('text', 'N/A')[:100]}...")
        print(f"  Profile: {post.get('profile_link', 'N/A')}")
        print(f"  Job Link: {post.get('job_application_link', 'N/A')}")


# Example 2: Using cookies directly
def example_with_cookies():
    """Example using cookies directly."""
    cookies = [
        {
            "name": "li_at",
            "value": "YOUR_COOKIE_VALUE",
            "domain": ".linkedin.com",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        }
    ]
    
    scraper = LinkedInScraper(cookies=cookies)
    url = "https://www.linkedin.com/search/results/content/?keywords=python"
    posts = scraper.scrape_posts(url, max_scroll=3)
    scraper.posts_data = posts
    scraper.save_to_json('example_output.json')


if __name__ == '__main__':
    print("LinkedIn Scraper - Example Usage")
    print("=" * 50)
    print("\nTo use this example:")
    print("1. Export your LinkedIn cookies to 'linkedin_cookies.json'")
    print("2. Uncomment one of the example functions below")
    print("3. Run: python example_usage.py")
    print("\n" + "=" * 50)
    
    # Uncomment to run:
    # example_with_cookie_file()
    # example_with_cookies()

