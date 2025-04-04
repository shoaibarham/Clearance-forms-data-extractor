import os
import time
import pandas as pd
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SeajetsScraper:
    """
    A class to scrape itineraries and seat availability from the Seajets website
    for the Piraeus to Milos route within a specified date range.
    """
    
    def __init__(self):
        self.url = "https://www.seajets.com/"
        self.origin = "Piraeus"
        self.destination = "Milos"
        self.itineraries_data = []
        self.seats_data = []
        
    def setup_driver(self):
        """Set up the Selenium WebDriver with necessary options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        # Add options for Replit environment
        chrome_options.binary_location = "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium"
        
        # Create and return the webdriver
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    
    def date_range(self, start_date_str, end_date_str):
        """Generate a list of dates within the given range"""
        start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
        end_date = datetime.strptime(end_date_str, "%d/%m/%Y")
        
        date_list = []
        current_date = start_date
        
        while current_date <= end_date:
            date_list.append(current_date.strftime("%d/%m/%Y"))
            current_date += timedelta(days=1)
            
        return date_list
    
    def wait_for_element(self, driver, by, value, timeout=10):
        """Wait for an element to be visible on the page"""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.error(f"Timeout waiting for element: {value}")
            return None
    
    def click_element(self, driver, by, value, timeout=10):
        """Wait for an element to be clickable and then click it"""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            return True
        except TimeoutException:
            logger.error(f"Timeout waiting for clickable element: {value}")
            return False
    
    def scrape_seajets(self, start_date, end_date):
        """
        Main method to scrape Seajets website for itineraries and seat availability
        
        Args:
            start_date (str): Start date in DD/MM/YYYY format
            end_date (str): End date in DD/MM/YYYY format
            
        Returns:
            dict: Dictionary containing DataFrames with itineraries and seat availability
        """
        logger.info(f"Starting scrape for dates from {start_date} to {end_date}")
        
        # Reset data containers
        self.itineraries_data = []
        self.seats_data = []
        
        # Initialize webdriver
        driver = self.setup_driver()
        
        try:
            # Navigate to Seajets website
            driver.get(self.url)
            logger.info("Navigated to Seajets website")
            
            # Select English language
            self.select_english(driver)
            
            # Generate list of dates to scrape
            dates_to_scrape = self.date_range(start_date, end_date)
            
            for date_str in dates_to_scrape:
                logger.info(f"Processing date: {date_str}")
                
                # Navigate through the search form
                self.navigate_search_form(driver, date_str)
                
                # Scrape itineraries for this date
                self.scrape_itineraries(driver, date_str)
                
                # Go back to home page for next date
                driver.get(self.url)
                self.select_english(driver)
            
            # Convert data to DataFrames
            itineraries_df = pd.DataFrame(self.itineraries_data) if self.itineraries_data else pd.DataFrame()
            seats_df = pd.DataFrame(self.seats_data) if self.seats_data else pd.DataFrame()
            
            return {
                'itineraries': itineraries_df,
                'seats': seats_df
            }
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            raise
        finally:
            # Close the browser
            driver.quit()
    
    def select_english(self, driver):
        """Select English language on the website"""
        try:
            # Wait for language selector and click English
            language_selector = self.wait_for_element(driver, By.CSS_SELECTOR, ".language-selector")
            if language_selector:
                english_option = driver.find_element(By.XPATH, "//a[contains(text(), 'English')]")
                english_option.click()
                logger.info("Selected English language")
                time.sleep(2)  # Wait for language change to take effect
        except Exception as e:
            logger.error(f"Error selecting English language: {str(e)}")
    
    def navigate_search_form(self, driver, date_str):
        """Fill out and submit the search form"""
        try:
            # Select origin (Piraeus)
            origin_field = self.wait_for_element(driver, By.ID, "from_location")
            if origin_field:
                origin_field.click()
                origin_option = self.wait_for_element(driver, By.XPATH, f"//li[contains(text(), '{self.origin}')]")
                if origin_option:
                    origin_option.click()
                    logger.info(f"Selected origin: {self.origin}")
            
            # Select destination (Milos)
            destination_field = self.wait_for_element(driver, By.ID, "to_location")
            if destination_field:
                destination_field.click()
                destination_option = self.wait_for_element(driver, By.XPATH, f"//li[contains(text(), '{self.destination}')]")
                if destination_option:
                    destination_option.click()
                    logger.info(f"Selected destination: {self.destination}")
            
            # Select "ONE WAY TRIP"
            one_way_option = self.wait_for_element(driver, By.XPATH, "//label[contains(text(), 'ONE WAY')]")
            if one_way_option:
                one_way_option.click()
                logger.info("Selected ONE WAY TRIP")
            
            # Select date
            date_field = self.wait_for_element(driver, By.ID, "departure_date")
            if date_field:
                date_field.clear()
                date_field.send_keys(date_str)
                # Click OK on date picker
                date_ok_button = self.wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Ok')]")
                if date_ok_button:
                    date_ok_button.click()
                    logger.info(f"Selected date: {date_str}")
            
            # Keep default passengers (1)
            passengers_field = self.wait_for_element(driver, By.ID, "passengers")
            if passengers_field:
                passengers_field.click()
                # Click OK for passengers
                passengers_ok_button = self.wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Ok')]")
                if passengers_ok_button:
                    passengers_ok_button.click()
                    logger.info("Kept default passengers: 1")
            
            # Keep default vehicles (0)
            vehicles_field = self.wait_for_element(driver, By.ID, "vehicles")
            if vehicles_field:
                vehicles_field.click()
                # Click OK for vehicles
                vehicles_ok_button = self.wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Ok')]")
                if vehicles_ok_button:
                    vehicles_ok_button.click()
                    logger.info("Kept default vehicles: 0")
            
            # Click Search button
            search_button = self.wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Search')]")
            if search_button:
                search_button.click()
                logger.info("Clicked Search button")
                time.sleep(5)  # Wait for search results to load
            
        except Exception as e:
            logger.error(f"Error navigating search form: {str(e)}")
    
    def scrape_itineraries(self, driver, date_str):
        """Scrape itineraries for the given date"""
        try:
            # Wait for itineraries to load
            itineraries = self.wait_for_element(driver, By.CSS_SELECTOR, ".itineraries-container")
            if not itineraries:
                logger.warning(f"No itineraries found for date: {date_str}")
                return
            
            # Find all itineraries
            itinerary_elements = driver.find_elements(By.CSS_SELECTOR, ".itinerary-item")
            logger.info(f"Found {len(itinerary_elements)} itineraries for date: {date_str}")
            
            for index, itinerary in enumerate(itinerary_elements):
                try:
                    # Extract itinerary details
                    vessel_name = itinerary.find_element(By.CSS_SELECTOR, ".vessel-name").text
                    departure_time = itinerary.find_element(By.CSS_SELECTOR, ".departure-time").text
                    arrival_time = itinerary.find_element(By.CSS_SELECTOR, ".arrival-time").text
                    duration = itinerary.find_element(By.CSS_SELECTOR, ".duration").text
                    
                    # Check if this itinerary is available (people icon not grey)
                    people_icon = itinerary.find_element(By.CSS_SELECTOR, ".people-icon")
                    is_available = "grey" not in people_icon.get_attribute("class")
                    
                    # Record itinerary data
                    itinerary_data = {
                        'Date': date_str,
                        'Vessel': vessel_name,
                        'Departure Time': departure_time,
                        'Arrival Time': arrival_time,
                        'Duration': duration,
                        'Available': is_available
                    }
                    self.itineraries_data.append(itinerary_data)
                    logger.info(f"Recorded itinerary: {vessel_name} at {departure_time}")
                    
                    # If itinerary is available, click to see seat availability
                    if is_available:
                        # Click on the itinerary
                        itinerary.click()
                        logger.info(f"Clicked on itinerary: {vessel_name}")
                        time.sleep(2)
                        
                        # Click Next button
                        next_button = self.wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Next')]")
                        if next_button:
                            next_button.click()
                            logger.info("Clicked Next button")
                            time.sleep(3)
                            
                            # Scrape seat availability
                            self.scrape_seats(driver, date_str, vessel_name)
                            
                            # Go back to itineraries page
                            driver.back()
                            driver.back()
                            time.sleep(3)
                    else:
                        logger.info(f"Skipping unavailable itinerary: {vessel_name}")
                        
                except Exception as e:
                    logger.error(f"Error processing itinerary {index+1}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error scraping itineraries: {str(e)}")
    
    def scrape_seats(self, driver, date_str, vessel_name):
        """Scrape seat availability for the given itinerary"""
        try:
            # Wait for seat selection page to load
            seat_container = self.wait_for_element(driver, By.CSS_SELECTOR, ".seat-selection-container")
            if not seat_container:
                logger.warning(f"No seat selection container found for {vessel_name} on {date_str}")
                return
            
            # Find all seat categories
            seat_categories = driver.find_elements(By.CSS_SELECTOR, ".seat-category")
            logger.info(f"Found {len(seat_categories)} seat categories for {vessel_name}")
            
            for category in seat_categories:
                try:
                    # Extract category name and availability
                    category_name = category.find_element(By.CSS_SELECTOR, ".category-name").text
                    available_seats = category.find_element(By.CSS_SELECTOR, ".available-seats").text
                    
                    # Record seat data
                    seat_data = {
                        'Date': date_str,
                        'Vessel': vessel_name,
                        'Category': category_name,
                        'Available Seats': available_seats
                    }
                    self.seats_data.append(seat_data)
                    logger.info(f"Recorded seat availability: {category_name} - {available_seats}")
                    
                except Exception as e:
                    logger.error(f"Error processing seat category: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error scraping seats: {str(e)}")
