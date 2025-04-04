import os
import logging
from flask import Flask, render_template, request, jsonify, session
from scraper import SeajetsScraper
import pandas as pd
import json
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

@app.route('/')
def index():
    """Render the main page with the date range selector and RUN button"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """
    API endpoint to start the scraping process
    Expects start_date and end_date in the request
    """
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        logger.debug(f"Received scrape request for date range: {start_date} to {end_date}")
        
        # Validate dates
        try:
            datetime.strptime(start_date, '%d/%m/%Y')
            datetime.strptime(end_date, '%d/%m/%Y')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Please use DD/MM/YYYY format.'}), 400
        
        # Initialize scraper
        scraper = SeajetsScraper()
        
        # Start scraping process
        results = scraper.scrape_seajets(start_date, end_date)
        
        # Store results in session for the results page
        session['results'] = json.dumps({
            'itineraries': results['itineraries'].to_dict('records') if not results['itineraries'].empty else [],
            'seats': results['seats'].to_dict('records') if not results['seats'].empty else []
        })
        
        return jsonify({'status': 'success', 'message': 'Scraping completed successfully!'})
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def results():
    """Render the results page with the scraped data"""
    if 'results' not in session:
        return render_template('index.html', error="No results found. Please run a scrape first.")
    
    results = json.loads(session['results'])
    return render_template('results.html', 
                           itineraries=results['itineraries'],
                           seats=results['seats'])

@app.route('/export_csv', methods=['POST'])
def export_csv():
    """Export the scraped data as CSV files"""
    if 'results' not in session:
        return jsonify({'error': 'No results found'}), 400
    
    try:
        results = json.loads(session['results'])
        
        # Convert to DataFrames
        itineraries_df = pd.DataFrame(results['itineraries'])
        seats_df = pd.DataFrame(results['seats'])
        
        # Get current date for filename
        current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create CSV files
        itineraries_csv = itineraries_df.to_csv(index=False)
        seats_csv = seats_df.to_csv(index=False)
        
        return jsonify({
            'status': 'success',
            'itineraries_csv': itineraries_csv,
            'seats_csv': seats_csv,
            'filename_prefix': f"seajets_scrape_{current_date}"
        })
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        return jsonify({'error': str(e)}), 500
