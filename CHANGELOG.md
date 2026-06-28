# Changelog - LinkedIn Scraper

This file tracks significant changes, fixes, and issues encountered with the LinkedIn scraper.

## Format
- **Date**: YYYY-MM-DD
- **Issue**: Brief description
- **Symptoms**: What was observed
- **Root Cause**: What caused the issue
- **Solution**: How it was fixed
- **Files Changed**: Which files were modified

---

## 2026-01-31 - Fixed "No Posts Found" Issue

### Issue
Scraper returning 0 posts despite posts existing on LinkedIn page.

### Symptoms
- API response: `{"success": true, "posts": [], "count": 0}`
- Logs showed: "Warning: No posts found"
- Logs showed: "Found 0 elements matching" for all CSS selectors
- Debug HTML contained activity URNs (proving posts existed in HTML)

### Root Cause
1. **Early Return Bug**: JavaScript extraction code was placed AFTER an early `return []` statement, so it never executed when CSS selectors failed.
2. **LinkedIn Structure Change**: LinkedIn moved to React-based rendering, making traditional CSS selectors unreliable.
3. **Insufficient Wait Times**: React content needed more time to render before extraction.

### Solution
1. **Moved JavaScript Extraction**: Placed JavaScript extraction code BEFORE the early return (line ~1195 in `linkedin_scraper.py`)
2. **Added JavaScript-Based Extraction**: Implemented fallback that uses `page.evaluate()` to find posts by:
   - Text content length (50-10000 chars)
   - Presence of profile links (`/in/` URLs)
   - Post indicators (time stamps, actor elements)
   - Element visibility (bounding box checks)
3. **Improved Wait Times**: 
   - Added wait for network idle state
   - Increased wait after feed container found (10 seconds)
   - Added activity URN count check

### Files Changed
- `linkedin_scraper.py`: 
  - Lines ~1100-1200: Added JavaScript extraction logic
  - Line ~447: Improved wait times for React content
  - Line ~1195: Moved JS extraction before return statement

### Result
- Before: 0 posts returned
- After: 22-31 posts returned per request
- Extraction method: JavaScript-based (CSS selectors still tried first)

### Key Learnings
- LinkedIn uses React, so content loads dynamically
- Multiple extraction strategies are essential (CSS → JavaScript → Text patterns)
- Early returns can prevent fallback code from executing
- Activity URNs in HTML don't guarantee extractable DOM elements

---

## 2026-01-31 - Added .env File Support

### Issue
API key was hardcoded or required manual environment variable setup.

### Solution
- Added `python-dotenv` to `requirements.txt`
- Added `load_dotenv()` in `api.py` to automatically load `.env` file
- API key now loads from `LINKEDIN_SCRAPER_API_KEY` in `.env`

### Files Changed
- `requirements.txt`: Added `python-dotenv==1.0.0`
- `api.py`: Added `from dotenv import load_dotenv` and `load_dotenv()` call

---

## Future Issues to Track

### When Adding New Entries, Include:
1. **Date** of the issue
2. **Symptoms** - What was observed
3. **Root Cause** - Technical explanation
4. **Solution** - How it was fixed
5. **Files Changed** - Specific files and line numbers
6. **Prevention** - How to avoid in future

### Common Patterns to Watch For:
- LinkedIn UI structure changes (CSS selectors break)
- Cookie expiration (login redirects)
- Rate limiting (timeout errors)
- Browser/Playwright version issues
- Network/proxy connectivity problems

---

**Note**: Keep this file updated whenever significant issues are encountered or fixed. This helps with future troubleshooting and understanding the evolution of the scraper.
