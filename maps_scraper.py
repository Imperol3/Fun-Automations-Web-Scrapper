from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import *
from flask import Flask, request, jsonify, render_template
import time
import logging
import random
from typing import Dict, List, Optional
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

class RetryableError(Exception):
    """Error that can be retried"""
    pass

def setup_driver() -> webdriver.Chrome:
    """Setup Chrome driver with optimized settings for production."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--lang=en-US')
    
    # Randomize user agent from a pool
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0',
    ]
    chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    # Add experimental options
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Execute CDP commands to prevent detection
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": random.choice(user_agents)
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def random_sleep(min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
    """Sleep for a random amount of time to mimic human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def load_more_places(driver: webdriver.Chrome, container: webdriver.remote.webelement.WebElement, previous_count: int) -> bool:
    """Load more places using optimized keyboard navigation."""
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
        if not elements:
            return False
            
        last_element = elements[-1]
        
        # Move to element with random offset
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)
        ActionChains(driver).move_to_element_with_offset(last_element, offset_x, offset_y).click().perform()
        random_sleep(0.3, 0.7)
        
        # Simulate natural keyboard navigation
        for _ in range(random.randint(3, 7)):
            if random.random() < 0.2:  # 20% chance to use PAGE_DOWN
                ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform()
            else:
                ActionChains(driver).send_keys(Keys.DOWN).perform()
            random_sleep(0.2, 0.5)
        
        # Additional random scrolling
        scroll_amount = random.randint(300, 700)
        driver.execute_script(
            f"arguments[0].scrollBy(0, {scroll_amount});", 
            container
        )
        random_sleep()
        
        new_elements = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
        return len(new_elements) > previous_count
        
    except Exception as e:
        logger.error(f"Error in load_more_places: {str(e)}")
        if isinstance(e, (ElementClickInterceptedException, StaleElementReferenceException)):
            raise RetryableError("Retryable error in load_more_places")
        return False

def extract_place_info(driver: webdriver.Chrome, place: webdriver.remote.webelement.WebElement, 
                      wait: WebDriverWait) -> Optional[Dict]:
    """Extract comprehensive information about a place."""
    try:
        # Click with retry mechanism
        for _ in range(3):
            try:
                place.click()
                break
            except ElementClickInterceptedException:
                random_sleep()
                driver.execute_script("arguments[0].click();", place)
            except StaleElementReferenceException:
                return None
        
        random_sleep()
        
        # Extract basic information with wait conditions
        info = {}
        
        # Name (required field)
        try:
            info['name'] = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.DUwDvf.lfPIob"))
            ).text.strip()
        except TimeoutException:
            logger.warning("Could not find place name, skipping...")
            return None
            
        # Optional fields with default values
        info.update({
            'rating': None,
            'reviews': None,
            'address': None,
            'phone': None,
            'website': None,
            'hours': None,
            'category': None
        })
        
        # Try to extract optional fields
        try:
            info['rating'] = driver.find_element(By.CSS_SELECTOR, "span.MW4etd").text.strip()
        except NoSuchElementException:
            pass
            
        try:
            info['reviews'] = driver.find_element(By.CSS_SELECTOR, "span.F7nice").text.strip()
        except NoSuchElementException:
            pass
        
        # Extract address with better selector
        try:
            address_element = driver.find_element(
                By.CSS_SELECTOR, 
                'button[data-item-id="address"], div[data-item-id="address"]'
            )
            info['address'] = address_element.text.strip()
        except NoSuchElementException:
            pass
            
        # Extract phone number
        try:
            phone_element = driver.find_element(
                By.CSS_SELECTOR, 
                'button[data-item-id="phone"], div[data-item-id="phone"]'
            )
            info['phone'] = phone_element.text.strip()
        except NoSuchElementException:
            pass
            
        # Extract website
        try:
            website_element = driver.find_element(
                By.CSS_SELECTOR, 
                'a[data-item-id="authority"]'
            )
            info['website'] = website_element.get_attribute('href')
        except NoSuchElementException:
            pass
            
        # Extract category
        try:
            category_element = driver.find_element(
                By.CSS_SELECTOR,
                'button[jsaction="pane.rating.category"]'
            )
            info['category'] = category_element.text.strip()
        except NoSuchElementException:
            pass
            
        return info
        
    except Exception as e:
        logger.error(f"Error extracting place info: {str(e)}")
        if isinstance(e, (ElementClickInterceptedException, StaleElementReferenceException)):
            raise RetryableError("Retryable error in extract_place_info")
        return None

def scrape_google_maps(search_query: str, limit: int = 0) -> List[Dict]:
    """
    Scrape Google Maps with improved reliability and error handling.
    
    Args:
        search_query: Search term to look for
        limit: Maximum number of results (0 for unlimited)
        
    Returns:
        List of dictionaries containing place information
    """
    driver = None
    start_time = time.time()
    MAX_SCRAPE_TIME = 180  # Increased to 3 minutes for better results
    MAX_RETRIES = 3
    
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 15)
        
        # Navigate to Google Maps
        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        driver.get(url)
        random_sleep(2, 4)  # Variable initial wait
        
        # Wait for and get the results container
        container = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf"))
        )
        
        results = []
        seen_names = set()
        no_new_results_count = 0
        last_count = 0
        retry_count = 0
        
        while True:
            if time.time() - start_time > MAX_SCRAPE_TIME:
                logger.info("Reached maximum time limit")
                break
                
            try:
                # Get current visible places
                places = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
                current_count = len(places)
                
                logger.info(f"Found {current_count} places")
                
                # Process only new places
                for place in places[last_count:]:
                    try:
                        info = extract_place_info(driver, place, wait)
                        if info and info['name'] not in seen_names:
                            results.append(info)
                            seen_names.add(info['name'])
                            logger.info(f"Added: {info['name']} (Total: {len(results)})")
                            
                            if limit > 0 and len(results) >= limit:
                                return results
                    except RetryableError:
                        if retry_count < MAX_RETRIES:
                            retry_count += 1
                            random_sleep(1, 2)
                            continue
                        else:
                            logger.warning("Max retries reached for place, skipping...")
                    except Exception as e:
                        logger.error(f"Error processing place: {str(e)}")
                        continue
                
                # Update last_count
                last_count = current_count
                
                # Try to load more results
                try:
                    if not load_more_places(driver, container, current_count):
                        no_new_results_count += 1
                        if no_new_results_count >= 3:
                            logger.info("No more results found after multiple attempts")
                            break
                    else:
                        no_new_results_count = 0
                        retry_count = 0  # Reset retry count on successful load
                except RetryableError:
                    if retry_count < MAX_RETRIES:
                        retry_count += 1
                        random_sleep(1, 2)
                        continue
                    else:
                        logger.warning("Max retries reached for loading more places")
                        break
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                if retry_count < MAX_RETRIES:
                    retry_count += 1
                    random_sleep(2, 4)
                    continue
                else:
                    break
        
        logger.info(f"Scraping completed. Total results: {len(results)}")
        return results
        
    except Exception as e:
        logger.error(f"Fatal error during scraping: {str(e)}")
        return []
        
    finally:
        if driver:
            driver.quit()

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle scraping requests with improved error handling."""
    try:
        data = request.get_json()
        if not data or 'search_query' not in data:
            return jsonify({
                'error': 'Missing search_query parameter',
                'status': 'error'
            }), 400
        
        search_query = data['search_query']
        limit = int(data.get('limit', 0))
        
        if not search_query.strip():
            return jsonify({
                'error': 'Empty search query',
                'status': 'error'
            }), 400
        
        logger.info(f"Starting scrape for '{search_query}' with limit {limit}")
        results = scrape_google_maps(search_query, limit)
        
        response = {
            'status': 'success',
            'search_query': search_query,
            'results_count': len(results),
            'results': results,
            'message': 'Scraping completed successfully'
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500

if __name__ == '__main__':
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    app.run(debug=False, host='0.0.0.0', port=5000)
