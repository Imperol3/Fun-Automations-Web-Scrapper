from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
import asyncio
from typing import List, Optional, Dict
from pydantic import BaseModel
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class SearchRequest(BaseModel):
    search_query: str
    limit: int = 5

class Business(BaseModel):
    name: str
    rating: Optional[str]
    reviews: Optional[str]
    category: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    website: Optional[str]

async def scrape_maps(query: str, limit: int) -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to Google Maps
            await page.goto('https://www.google.com/maps')
            await page.wait_for_load_state('networkidle')
            
            # Accept cookies if present
            try:
                await page.click('button:has-text("Accept all")', timeout=5000)
            except:
                pass
            
            # Search for the query
            await page.fill('input[name="q"]', query)
            await page.press('input[name="q"]', 'Enter')
            await page.wait_for_load_state('networkidle')
            
            results = []
            seen_names = set()
            
            while len(results) < limit:
                # Extract business info
                cards = await page.query_selector_all('[role="article"]')
                
                for card in cards:
                    if len(results) >= limit:
                        break
                        
                    try:
                        # Click the card to load details
                        await card.click()
                        await page.wait_for_load_state('networkidle')
                        
                        # Extract business details
                        name = await card.evaluate('el => el.querySelector("h3")?.textContent || ""')
                        
                        if not name or name in seen_names:
                            continue
                            
                        seen_names.add(name)
                        
                        info = {
                            'name': name,
                            'rating': await page.evaluate('() => document.querySelector("[role=img]")?.ariaLabel?.match(/([0-9.]+)/)?.[0] || ""'),
                            'reviews': await page.evaluate('() => document.querySelector("[role=img]")?.ariaLabel?.match(/([0-9,]+) reviews/)?.[1] || ""'),
                            'category': await page.evaluate('() => Array.from(document.querySelectorAll("button")).find(el => el.textContent?.includes("·"))?.textContent?.split("·")?.[1]?.trim() || ""'),
                            'address': await page.evaluate('() => document.querySelector("button[data-item-id*=address]")?.textContent || ""'),
                            'phone': await page.evaluate('() => document.querySelector("button[data-item-id*=phone]")?.textContent || ""'),
                            'website': await page.evaluate('() => document.querySelector("a[data-item-id*=website]")?.href || ""')
                        }
                        
                        results.append(info)
                        
                    except Exception as e:
                        logger.warning(f"Error extracting business details: {e}")
                        continue
                
                if len(results) < limit:
                    try:
                        # Scroll to load more
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await page.wait_for_timeout(1000)
                    except:
                        break
            
            return results
            
        finally:
            await browser.close()

@app.post("/scrape")
async def scrape(request: SearchRequest):
    try:
        results = await scrape_maps(request.search_query, request.limit)
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
