#!/usr/bin/env python3
"""Simple test to verify Playwright browser can launch."""

from playwright.sync_api import sync_playwright
import time

def test_browser(browser_type, headless=False):
    """Test a specific browser type."""
    print(f"\n{'='*50}")
    print(f"Testing {browser_type} (headless={headless})...")
    print(f"{'='*50}")
    
    try:
        with sync_playwright() as p:
            print(f"1. Playwright context created")
            
            if browser_type == 'chromium':
                browser = p.chromium.launch(
                    headless=headless,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
            elif browser_type == 'firefox':
                browser = p.firefox.launch(headless=headless)
            elif browser_type == 'webkit':
                browser = p.webkit.launch(headless=headless)
            else:
                print(f"Unknown browser type: {browser_type}")
                return False
            
            print(f"2. {browser_type.capitalize()} browser launched")
            time.sleep(0.5)  # Small delay
            
            context = browser.new_context()
            print(f"3. Context created")
            time.sleep(0.5)
            
            page = context.new_page()
            print(f"4. Page created")
            
            page.goto('https://www.google.com', timeout=30000)
            print(f"5. Navigated to Google")
            
            time.sleep(2)
            print(f"6. ✅ {browser_type.capitalize()} test successful!")
            
            browser.close()
            print(f"7. Browser closed")
            return True
            
    except Exception as e:
        print(f"❌ ERROR with {browser_type}: {str(e)}")
        return False

# Test all browsers
print("Testing different browsers to find one that works...")

# Try headless first (more stable)
results = {}
for browser in ['chromium', 'firefox', 'webkit']:
    results[browser] = test_browser(browser, headless=True)
    time.sleep(1)

print("\n" + "="*50)
print("RESULTS:")
print("="*50)
for browser, success in results.items():
    status = "✅ WORKS" if success else "❌ FAILED"
    print(f"{browser.capitalize()}: {status}")

# If headless works, try non-headless
working_browser = None
for browser, success in results.items():
    if success:
        working_browser = browser
        break

if working_browser:
    print(f"\n✅ Found working browser: {working_browser}")
    print(f"Trying {working_browser} in non-headless mode...")
    test_browser(working_browser, headless=False)
else:
    print("\n❌ No browsers working. Check Playwright installation.")

