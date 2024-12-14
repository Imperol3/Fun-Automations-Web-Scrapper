from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import *
from flask import Flask, request, jsonify
import time
import logging
import random
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import threading
import json
from datetime import datetime
import os
import re
import sys
from logging.handlers import RotatingFileHandler

# Configure logging at the very start
logging.basicConfig(level=logging.INFO)

def setup_logging():
    """Configure logging with real-time updates and detailed information."""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure scraper logger
    scraper_logger = logging.getLogger('scraper')
    scraper_logger.setLevel(logging.INFO)
    scraper_logger.handlers = []  # Clear existing handlers

    # File handler for scraper
    scraper_file_handler = RotatingFileHandler(
        'logs/scraper.log',
        mode='a',
        maxBytes=5*1024*1024,
        backupCount=2,
        delay=False
    )
    scraper_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    scraper_file_handler.setFormatter(scraper_formatter)
    scraper_logger.addHandler(scraper_file_handler)

    # Console handler for scraper
    scraper_console = logging.StreamHandler(sys.stdout)
    scraper_console.setFormatter(scraper_formatter)
    scraper_logger.addHandler(scraper_console)

    # Configure results logger
    results_logger = logging.getLogger('results')
    results_logger.setLevel(logging.INFO)
    results_logger.handlers = []

    # File handler for results
    results_file_handler = RotatingFileHandler(
        'logs/results.log',
        mode='a',
        maxBytes=5*1024*1024,
        backupCount=2,
        delay=False
    )
    results_formatter = logging.Formatter('%(asctime)s - %(message)s')
    results_file_handler.setFormatter(results_formatter)
    results_logger.addHandler(results_file_handler)

    # Console handler for results
    results_console = logging.StreamHandler(sys.stdout)
    results_console.setFormatter(results_formatter)
    results_logger.addHandler(results_console)

    # Ensure all handlers flush immediately
    for logger in [scraper_logger, results_logger]:
        for handler in logger.handlers:
            handler.flush()
            if isinstance(handler, RotatingFileHandler):
                handler.doRollover()

    return scraper_logger, results_logger

# Initialize loggers
scraper_logger, results_logger = setup_logging()

app = Flask(__name__)

class RetryableError(Exception):
    """Error that can be retried"""
    pass

def extract_email_from_text(text: str) -> Optional[str]:
    """Extract email from text using regex."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None

def extract_hours(driver: webdriver.Chrome) -> Dict:
    """Extract detailed business hours."""
    hours = {}
    try:
        # Click on hours button if it exists
        hours_button = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="oh"]')
        hours_button.click()
        time.sleep(1)
        
        # Extract hours table
        hours_rows = driver.find_elements(By.CSS_SELECTOR, 'table.WgFkxc tbody tr')
        for row in hours_rows:
            try:
                day = row.find_element(By.CSS_SELECTOR, 'th').text.strip()
                time_ranges = row.find_elements(By.CSS_SELECTOR, 'td li')
                
                if time_ranges:
                    hours[day] = [range.text.strip() for range in time_ranges]
                else:
                    time_text = row.find_element(By.CSS_SELECTOR, 'td').text.strip()
                    hours[day] = [time_text]
            except NoSuchElementException:
                continue
        
        # Check for holiday hours or special hours
        special_hours = driver.find_elements(By.CSS_SELECTOR, 'div.G8aQO')
        if special_hours:
            hours['special_hours'] = [hour.text.strip() for hour in special_hours]
            
    except Exception as e:
        scraper_logger.error(f"Error extracting hours: {str(e)}")
    
    return hours

def extract_about_section(driver: webdriver.Chrome) -> Dict:
    """Extract comprehensive about section information."""
    about_info = {}
    try:
        # Click on about section if it exists
        about_button = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="about"]')
        about_button.click()
        time.sleep(1)
        
        # Extract all information sections
        sections = driver.find_elements(By.CSS_SELECTOR, 'div.Io6YTe')
        for section in sections:
            try:
                label = section.find_element(By.CSS_SELECTOR, 'div.kR99db').text.strip()
                value = section.find_element(By.CSS_SELECTOR, 'div.gYNNTe').text.strip()
                about_info[label] = value
            except NoSuchElementException:
                continue
            
        # Extract additional details
        details = driver.find_elements(By.CSS_SELECTOR, 'div.HeZRrf')
        if details:
            about_info['additional_details'] = [detail.text.strip() for detail in details]
            
    except Exception as e:
        scraper_logger.error(f"Error extracting about section: {str(e)}")
    
    return about_info

def extract_amenities(driver: webdriver.Chrome) -> List[str]:
    """Extract all available amenities."""
    amenities = []
    try:
        # Look for amenities section
        amenities_elements = driver.find_elements(By.CSS_SELECTOR, 'div.ty7HZb')
        for element in amenities_elements:
            amenity = element.text.strip()
            if amenity:
                amenities.append(amenity)
                
        # Try to expand and get more amenities if available
        more_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label*="more"]')
        if more_button:
            more_button.click()
            time.sleep(1)
            
            additional_amenities = driver.find_elements(By.CSS_SELECTOR, 'div.ty7HZb')
            for element in additional_amenities:
                amenity = element.text.strip()
                if amenity and amenity not in amenities:
                    amenities.append(amenity)
                    
    except Exception as e:
        scraper_logger.error(f"Error extracting amenities: {str(e)}")
    
    return amenities

def extract_reviews_summary(driver: webdriver.Chrome) -> Dict:
    """Extract detailed review information."""
    reviews_info = {
        'rating': None,
        'total_reviews': None,
        'rating_breakdown': {},
        'recent_reviews': []
    }
    
    try:
        # Get overall rating and total reviews
        rating_element = driver.find_element(By.CSS_SELECTOR, 'span.MW4etd')
        reviews_info['rating'] = rating_element.text.strip()
        
        total_reviews_element = driver.find_element(By.CSS_SELECTOR, 'span.F7nice')
        reviews_info['total_reviews'] = total_reviews_element.text.strip()
        
        # Get rating breakdown
        rating_bars = driver.find_elements(By.CSS_SELECTOR, 'div.VfPpkd-vQzf8d')
        for bar in rating_bars:
            try:
                stars = bar.find_element(By.CSS_SELECTOR, 'div.DU9Pgb').text.strip()
                percentage = bar.find_element(By.CSS_SELECTOR, 'div.STQFb').get_attribute('style')
                reviews_info['rating_breakdown'][stars] = percentage
            except NoSuchElementException:
                continue
        
        # Get recent reviews
        review_elements = driver.find_elements(By.CSS_SELECTOR, 'div.jJc9Ad')
        for review in review_elements[:5]:  # Get first 5 reviews
            try:
                review_info = {
                    'author': review.find_element(By.CSS_SELECTOR, 'div.d4r55').text.strip(),
                    'rating': review.find_element(By.CSS_SELECTOR, 'span.kvMYJc').get_attribute('aria-label'),
                    'text': review.find_element(By.CSS_SELECTOR, 'span.wiI7pd').text.strip(),
                    'time': review.find_element(By.CSS_SELECTOR, 'span.rsqaWe').text.strip()
                }
                reviews_info['recent_reviews'].append(review_info)
            except NoSuchElementException:
                continue
                
    except Exception as e:
        scraper_logger.error(f"Error extracting reviews summary: {str(e)}")
    
    return reviews_info

def extract_place_info(driver, place, wait) -> Dict:
    """Extract information about a place."""
    try:
        scraper_logger.info("="*50)
        scraper_logger.info("Starting extraction of new place")
        scraper_logger.handlers[0].flush()
        
        # Click on the place to open details
        place.click()
        random_sleep(2, 3)
        
        info = {}
        
        # Extract basic information
        try:
            name_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.DUwDvf")))
            info['name'] = name_elem.text.strip()
            scraper_logger.info(f"Found business: {info['name']}")
            scraper_logger.handlers[0].flush()
        except Exception as e:
            scraper_logger.warning(f"Could not extract name: {str(e)}")
            scraper_logger.handlers[0].flush()
            return None

        # Extract rating and reviews
        try:
            rating_elem = driver.find_element(By.CSS_SELECTOR, "div.F7nice span.ceNzKf")
            info['rating'] = rating_elem.text.strip()
            reviews_elem = driver.find_element(By.CSS_SELECTOR, "div.F7nice span.RDApEe")
            info['reviews'] = reviews_elem.text.strip()
            scraper_logger.info(f"Rating: {info['rating']}, Reviews: {info['reviews']}")
            scraper_logger.handlers[0].flush()
        except:
            info['rating'] = None
            info['reviews'] = None
            scraper_logger.info("No rating/reviews found")
            scraper_logger.handlers[0].flush()

        # Extract address
        try:
            address_button = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]')
            info['address'] = address_button.text.strip()
            scraper_logger.info(f"Address: {info['address']}")
            scraper_logger.handlers[0].flush()
        except:
            info['address'] = None
            scraper_logger.info("No address found")
            scraper_logger.handlers[0].flush()

        # Extract website
        try:
            website_button = driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            info['website'] = website_button.get_attribute('href')
            scraper_logger.info(f"Website: {info['website']}")
            scraper_logger.handlers[0].flush()
        except:
            info['website'] = None
            scraper_logger.info("No website found")
            scraper_logger.handlers[0].flush()

        # Extract phone
        try:
            phone_button = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id^="phone:"]')
            info['phone'] = phone_button.text.strip()
            scraper_logger.info(f"Phone: {info['phone']}")
            scraper_logger.handlers[0].flush()
        except:
            info['phone'] = None
            scraper_logger.info("No phone found")
            scraper_logger.handlers[0].flush()

        # Extract category
        try:
            category_elem = driver.find_element(By.CSS_SELECTOR, 'button[jsaction="pane.rating.category"]')
            info['category'] = category_elem.text.strip()
            scraper_logger.info(f"Category: {info['category']}")
            scraper_logger.handlers[0].flush()
        except:
            info['category'] = None
            scraper_logger.info("No category found")
            scraper_logger.handlers[0].flush()

        # Extract hours
        try:
            hours_button = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="oh"]')
            info['hours'] = hours_button.text.strip()
            scraper_logger.info(f"Hours: {info['hours']}")
            scraper_logger.handlers[0].flush()
        except:
            info['hours'] = None
            scraper_logger.info("No hours found")
            scraper_logger.handlers[0].flush()

        # Log the complete business details
        scraper_logger.info("-"*50)
        scraper_logger.info("Completed extraction of place")
        scraper_logger.info("="*50)
        scraper_logger.handlers[0].flush()

        # Log to results file
        results_logger.info("\n" + "="*50)
        results_logger.info(f"Business Details - {info['name']}")
        results_logger.info("-"*50)
        results_logger.info(json.dumps(info, indent=2, ensure_ascii=False))
        results_logger.info("="*50)
        results_logger.handlers[0].flush()

        return info

    except Exception as e:
        scraper_logger.error(f"Error extracting place info: {str(e)}")
        scraper_logger.handlers[0].flush()
        return None

def scrape_google_maps(search_query: str, limit: int = 0) -> List[Dict]:
    """
    Scrape Google Maps with improved reliability and error handling.
    """
    driver = None
    start_time = time.time()
    MAX_SCRAPE_TIME = 180
    MAX_RETRIES = 3
    
    try:
        scraper_logger.info("\n" + "="*50)
        scraper_logger.info(f"Starting new search for: {search_query}")
        scraper_logger.info(f"Requested limit: {limit}")
        scraper_logger.info("="*50 + "\n")
        scraper_logger.handlers[0].flush()
        
        driver = setup_driver()
        wait = WebDriverWait(driver, 15)
        
        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        driver.get(url)
        scraper_logger.info(f"Navigating to: {url}")
        scraper_logger.handlers[0].flush()
        random_sleep(2, 4)
        
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
                scraper_logger.info("Reached maximum time limit")
                scraper_logger.handlers[0].flush()
                break
                
            try:
                places = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
                current_count = len(places)
                
                scraper_logger.info(f"Found {current_count} places")
                scraper_logger.handlers[0].flush()
                
                for place in places[last_count:]:
                    try:
                        info = extract_place_info(driver, place, wait)
                        if info and info['name'] not in seen_names:
                            results.append(info)
                            seen_names.add(info['name'])
                            scraper_logger.info(f"Added: {info['name']} (Total: {len(results)})")
                            scraper_logger.handlers[0].flush()
                            
                            if limit > 0 and len(results) >= limit:
                                scraper_logger.info(f"Reached requested limit of {limit} results")
                                scraper_logger.handlers[0].flush()
                                return results
                                
                    except RetryableError:
                        if retry_count < MAX_RETRIES:
                            retry_count += 1
                            random_sleep(1, 2)
                            continue
                        else:
                            scraper_logger.warning("Max retries reached for place, skipping...")
                            scraper_logger.handlers[0].flush()
                    except Exception as e:
                        scraper_logger.error(f"Error processing place: {str(e)}")
                        scraper_logger.handlers[0].flush()
                        continue
                
                last_count = current_count
                
                try:
                    if not load_more_places(driver, container, current_count):
                        no_new_results_count += 1
                        if no_new_results_count >= 3:
                            scraper_logger.info("No more results found after multiple attempts")
                            scraper_logger.handlers[0].flush()
                            break
                    else:
                        no_new_results_count = 0
                        retry_count = 0
                except RetryableError:
                    if retry_count < MAX_RETRIES:
                        retry_count += 1
                        random_sleep(1, 2)
                        continue
                    else:
                        scraper_logger.warning("Max retries reached for loading more places")
                        scraper_logger.handlers[0].flush()
                        break
                
            except Exception as e:
                scraper_logger.error(f"Error in main loop: {str(e)}")
                scraper_logger.handlers[0].flush()
                if retry_count < MAX_RETRIES:
                    retry_count += 1
                    random_sleep(2, 4)
                    continue
                else:
                    break
        
        # Log final summary
        time_taken = time.time() - start_time
        summary = f"""
Search Summary:
--------------
Query: {search_query}
Total results found: {len(results)}
Time taken: {time_taken:.2f} seconds
--------------
"""
        scraper_logger.info(summary)
        scraper_logger.handlers[0].flush()
        
        # Log final results
        results_logger.info("\n" + "="*50)
        results_logger.info("FINAL SEARCH RESULTS")
        results_logger.info(f"Query: {search_query}")
        results_logger.info(f"Total Results: {len(results)}")
        results_logger.info("-"*50)
        results_logger.info(json.dumps(results, indent=2, ensure_ascii=False))
        results_logger.info("="*50 + "\n")
        results_logger.handlers[0].flush()
        
        return results
        
    except Exception as e:
        error_msg = f"Fatal error during scraping: {str(e)}"
        scraper_logger.error(error_msg)
        scraper_logger.handlers[0].flush()
        return []
        
    finally:
        if driver:
            driver.quit()

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
        scraper_logger.error(f"Error in load_more_places: {str(e)}")
        if isinstance(e, (ElementClickInterceptedException, StaleElementReferenceException)):
            raise RetryableError("Retryable error in load_more_places")
        return False

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
        error_msg = f"API error: {str(e)}"
        scraper_logger.error(error_msg)
        return jsonify({
            'error': str(e),
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500

if __name__ == '__main__':
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Clear previous log files
    with open('logs/scraper.log', 'w') as f:
        f.write(f"Starting new scraping session at {datetime.now().isoformat()}\n")
    with open('logs/results.log', 'w') as f:
        f.write(f"Starting new results log at {datetime.now().isoformat()}\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000)
