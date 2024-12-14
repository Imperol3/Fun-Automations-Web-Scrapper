from fastapi import FastAPI, HTTPException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from pydantic import BaseModel
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

class SearchRequest(BaseModel):
    search_query: str
    limit: int = 5

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    return webdriver.Chrome(options=chrome_options)

def scrape_maps(query: str, limit: int) -> List[Dict]:
    driver = setup_driver()
    wait = WebDriverWait(driver, 20)
    results = []
    
    try:
        logger.info(f"Starting scrape for query: {query}")
        # Navigate to Google Maps
        driver.get(f"https://www.google.com/maps/search/{query}")
        logger.info("Navigated to Google Maps")
        
        # Wait for results to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[role='article']")))
        logger.info("Initial results loaded")
        
        while len(results) < limit:
            # Get all business cards
            cards = driver.find_elements(By.CSS_SELECTOR, "[role='article']")
            logger.info(f"Found {len(cards)} cards")
            
            for card in cards[len(results):]:
                if len(results) >= limit:
                    break
                
                try:
                    # Click the card to load details
                    driver.execute_script("arguments[0].scrollIntoView(true);", card)
                    driver.execute_script("arguments[0].click();", card)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
                    
                    # Extract business details
                    info = {
                        'name': driver.find_element(By.CSS_SELECTOR, "h1").text,
                        'rating': driver.find_element(By.CSS_SELECTOR, "span.fontDisplayLarge").text if len(driver.find_elements(By.CSS_SELECTOR, "span.fontDisplayLarge")) > 0 else None,
                        'reviews': driver.find_element(By.CSS_SELECTOR, "button[jsaction*='pane.rating.moreReviews']").text if len(driver.find_elements(By.CSS_SELECTOR, "button[jsaction*='pane.rating.moreReviews']")) > 0 else None,
                        'category': driver.find_element(By.CSS_SELECTOR, "button[jsaction*='pane.rating.category']").text if len(driver.find_elements(By.CSS_SELECTOR, "button[jsaction*='pane.rating.category']")) > 0 else None,
                        'address': driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='address']").text if len(driver.find_elements(By.CSS_SELECTOR, "button[data-item-id*='address']")) > 0 else None,
                        'phone': driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='phone']").text if len(driver.find_elements(By.CSS_SELECTOR, "button[data-item-id*='phone']")) > 0 else None,
                        'website': driver.find_element(By.CSS_SELECTOR, "a[data-item-id*='authority']").get_attribute('href') if len(driver.find_elements(By.CSS_SELECTOR, "a[data-item-id*='authority']")) > 0 else None
                    }
                    
                    results.append(info)
                    logger.info(f"Successfully scraped: {info['name']}")
                    
                except Exception as e:
                    logger.error(f"Error extracting business details: {str(e)}")
                    continue
            
            if len(results) < limit:
                # Scroll to load more
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                driver.implicitly_wait(2)
        
        logger.info(f"Scraping completed. Found {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        driver.quit()

@app.post("/scrape")
def scrape(request: SearchRequest):
    try:
        logger.info(f"Received scrape request for: {request.search_query}")
        results = scrape_maps(request.search_query, request.limit)
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}
