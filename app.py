import os
import logging
import io
import base64
from flask import Flask, render_template, request, jsonify, session
from bs_scraper import SeajetsScraper  # Using the new scraper
import pandas as pd
import json
import traceback
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

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
    """Export the scraped data as CSV and Excel files"""
    logger.debug("Export request received")
    if 'results' not in session:
        logger.error("No results found in session")
        return jsonify({'error': 'No results found'}), 400
    
    try:
        logger.debug("Loading results from session")
        results = json.loads(session['results'])
        
        # Convert to DataFrames
        itineraries_df = pd.DataFrame(results['itineraries'])
        seats_df = pd.DataFrame(results['seats'])
        
        logger.debug(f"Data loaded: {len(itineraries_df)} itineraries, {len(seats_df)} seat records")
        
        # Get current date for filename
        current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_prefix = f"seajets_scrape_{current_date}"
        
        # Create CSV files
        logger.debug("Converting to CSV")
        itineraries_csv = itineraries_df.to_csv(index=False)
        seats_csv = seats_df.to_csv(index=False)
        
        # Create Excel file with multiple sheets
        logger.debug("Creating Excel file")
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Write the DataFrames to Excel
            itineraries_df.to_excel(writer, sheet_name='Itineraries', index=False)
            seats_df.to_excel(writer, sheet_name='Seat Availability', index=False)
            
            # Get the workbook and apply styling
            workbook = writer.book
            
            # Style the Itineraries sheet
            itineraries_sheet = workbook['Itineraries']
            header_fill = PatternFill(start_color="0052CC", end_color="0052CC", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            
            for cell in itineraries_sheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center')
            
            # Auto-adjust column widths
            for column in itineraries_sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                itineraries_sheet.column_dimensions[column_letter].width = adjusted_width
            
            # Style the Seats sheet
            seats_sheet = workbook['Seat Availability']
            for cell in seats_sheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center')
            
            # Auto-adjust column widths
            for column in seats_sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                seats_sheet.column_dimensions[column_letter].width = adjusted_width
        
        # Get the Excel bytes
        excel_buffer.seek(0)
        excel_data = excel_buffer.read()
        excel_base64 = base64.b64encode(excel_data).decode('utf-8')
        
        logger.debug("Sending export response")
        response_data = {
            'status': 'success',
            'itineraries_csv': itineraries_csv,
            'seats_csv': seats_csv,
            'excel_data': excel_base64,
            'filename_prefix': filename_prefix
        }
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
