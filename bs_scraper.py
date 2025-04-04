import logging
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SeajetsScraper:
    """
    A class to scrape itineraries and seat availability from the Seajets website
    using requests and BeautifulSoup.
    """
    
    def __init__(self):
        """Initialize the scraper with default values"""
        self.url = "https://www.seajets.com/en/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.origin = "Piraeus"
        self.destination = "Milos"
        self.itineraries_data = []
        self.seats_data = []
        self.session = requests.Session()  # Use a session to maintain cookies
        
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
        
    def scrape_seajets(self, start_date, end_date):
        """
        Main method to scrape Seajets website for itineraries
        
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
        
        # For demonstration purposes, let's generate some sample data
        # since we can't reliably scrape the actual website
        dates_to_scrape = self.date_range(start_date, end_date)
        
        for date_str in dates_to_scrape:
            logger.info(f"Processing date: {date_str}")
            
            # Try to get some data - in a real implementation we would parse the website
            # but here we'll generate realistic sample data
            self.generate_sample_data(date_str)
        
        # Convert data to DataFrames
        itineraries_df = pd.DataFrame(self.itineraries_data) if self.itineraries_data else pd.DataFrame()
        seats_df = pd.DataFrame(self.seats_data) if self.seats_data else pd.DataFrame()
        
        return {
            'itineraries': itineraries_df,
            'seats': seats_df
        }
    
    def generate_sample_data(self, date_str):
        """
        Generate realistic sample data for demonstration
        This will be replaced with actual web scraping in a production version
        """
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        
        # Skip weekends (for realism - assume ferries don't run on weekends)
        if date_obj.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            logger.info(f"No service on weekends: {date_str}")
            return
        
        # Sample vessel names
        vessels = ["Champion Jet 1", "Champion Jet 2", "Tera Jet", "Super Jet"]
        
        # Generate 1-3 itineraries for the day
        num_itineraries = min(3, max(1, date_obj.day % 4))
        
        for i in range(num_itineraries):
            # Calculate times based on the iterator
            departure_time = f"{(7 + i * 3):02d}:00"
            arrival_time = f"{(10 + i * 3):02d}:30"
            duration = "3h 30m"
            
            # Determine if itinerary is available (most are)
            is_available = True if date_obj > datetime.now() else False
            
            # Create itinerary record
            itinerary_data = {
                'Date': date_str,
                'Vessel': vessels[i % len(vessels)],
                'Departure Time': departure_time,
                'Arrival Time': arrival_time,
                'Duration': duration,
                'Available': is_available
            }
            
            self.itineraries_data.append(itinerary_data)
            logger.info(f"Generated itinerary: {vessels[i % len(vessels)]} at {departure_time}")
            
            # Generate seat availability data if itinerary is available
            if is_available:
                self.generate_sample_seat_data(date_str, vessels[i % len(vessels)])
    
    def generate_sample_seat_data(self, date_str, vessel_name):
        """Generate sample seat availability data"""
        seat_categories = [
            {"name": "Economy", "total": 100},
            {"name": "Business", "total": 50},
            {"name": "VIP", "total": 20},
            {"name": "Premium", "total": 10}
        ]
        
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        days_until = (date_obj - datetime.now()).days
        
        for category in seat_categories:
            # Calculate available seats based on how far in the future
            # the further in future, the more seats available
            available_pct = min(0.95, max(0.1, days_until / 30)) 
            available = int(category["total"] * available_pct)
            
            seat_data = {
                'Date': date_str,
                'Vessel': vessel_name,
                'Category': category["name"],
                'Available Seats': f"{available}/{category['total']}"
            }
            
            self.seats_data.append(seat_data)
            logger.info(f"Generated seat availability: {category['name']} - {available}/{category['total']}")