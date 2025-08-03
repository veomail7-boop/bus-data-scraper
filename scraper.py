import os
import configparser
import logging
from time import sleep
from bs4 import BeautifulSoup
from utils import (
    fetch_html, parse_bus_from_card, parse_bus_detail, 
    download_image, write_csv, clean_time_string, sanitize_filename
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

def main():
    """Main scraping function"""
    # Load configuration
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    base_url = config['DEFAULT'].get('base_url')
    start_page = config['DEFAULT'].getint('start_page')
    end_page = config['DEFAULT'].getint('end_page')
    csv_file = config['DEFAULT'].get('csv_file')
    image_dir = config['DEFAULT'].get('image_dir')
    timeout = config['DEFAULT'].getint('timeout')
    retry_count = config['DEFAULT'].getint('retry_count')
    
    # Ensure output directories exist
    if not os.path.exists(os.path.dirname(csv_file)):
        os.makedirs(os.path.dirname(csv_file))
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    
    all_data = []
    total_buses = 0
    successful_downloads = 0
    
    logging.info("Starting bus data scraping...")
    logging.info(f"Processing pages {start_page} to {end_page}")
    
    # Process each page
    for page in range(start_page, end_page + 1):
        if page == 1:
            # First page is the main URL without page parameter
            url = base_url
        else:
            url = f"{base_url}?page={page}"
        
        logging.info(f"Processing page {page}: {url}")
        
        # Fetch page HTML
        html = fetch_html(url, timeout=timeout, retry_count=retry_count)
        if not html:
            logging.error(f"Failed to fetch page: {url}")
            continue
        
        # Parse the page
        soup = BeautifulSoup(html, 'lxml')
        
        # Find all bus card links
        bus_cards = soup.find_all('a', href=True)
        page_buses = 0
        
        for card in bus_cards:
            # Check if this is a valid bus card (has image and bus info)
            if not card.find('img') or not card.find('h4'):
                continue
            
            # Check if href contains bus route pattern
            href = card.get('href', '')
            if '/bus/' not in href:
                continue
            
            try:
                # Parse basic bus information
                basic_data = parse_bus_from_card(card)
                
                if not basic_data.get('bus_name') or not basic_data.get('registration_number'):
                    logging.warning(f"Skipping bus card with missing basic info")
                    continue
                
                logging.info(f"Processing bus: {basic_data.get('bus_name')} ({basic_data.get('registration_number')})")
                
                # Fetch detailed information
                detail_data = {}
                if basic_data.get('detail_url'):
                    detail_html = fetch_html(basic_data['detail_url'], timeout=timeout, retry_count=retry_count)
                    if detail_html:
                        detail_data = parse_bus_detail(detail_html)
                    else:
                        logging.warning(f"Could not fetch detail page for {basic_data.get('bus_name')}")
                
                # Merge basic and detailed data
                combined_data = {**basic_data, **detail_data}
                
                # Download bus image
                if combined_data.get('image_url') and combined_data.get('bus_name') and combined_data.get('registration_number'):
                    try:
                        # Get file extension from URL
                        image_url = combined_data['image_url']
                        ext = image_url.split('.')[-1] if '.' in image_url else 'jpg'
                        
                        # Create sanitized filename
                        bus_name = sanitize_filename(combined_data['bus_name'])
                        reg_number = sanitize_filename(combined_data['registration_number'])
                        image_filename = f"{bus_name}_{reg_number}.{ext}"
                        save_path = os.path.join(image_dir, image_filename)
                        
                        if download_image(image_url, save_path):
                            successful_downloads += 1
                            combined_data['image_filename'] = image_filename
                    except Exception as e:
                        logging.error(f"Error processing image for {combined_data.get('bus_name')}: {e}")
                
                # Prepare CSV record with all required columns
                record = {
                    'Bus Name': combined_data.get('bus_name', ''),
                    'Bus Number': combined_data.get('registration_number', ''),
                    'Route': combined_data.get('route', ''),
                    'All Stoppage': combined_data.get('all_stoppage', ''),
                    'Stoppage Time': combined_data.get('stoppage_time', ''),
                    'Up Time': combined_data.get('up_time', ''),
                    'Down Time': combined_data.get('down_time', ''),
                    'AlternateName': combined_data.get('alternate_name', ''),
                    'Agency Name': combined_data.get('agency_name', ''),
                    'Bus Type': combined_data.get('bus_type', ''),
                    'Contact Number': combined_data.get('contact_number', ''),
                    'Alternate Number': combined_data.get('alternate_number', ''),
                    'Depot Name': combined_data.get('depot_name', ''),
                    'Destination': combined_data.get('destination', '')
                }
                
                all_data.append(record)
                total_buses += 1
                page_buses += 1
                
                # Small delay between bus processing
                sleep(0.5)
                
            except Exception as e:
                logging.error(f"Error processing bus card: {e}")
                continue
        
        logging.info(f"Page {page} completed. Found {page_buses} buses.")
        
        # Delay between pages to be respectful to the server
        sleep(2)
    
    # Write all data to CSV
    if all_data:
        write_csv(all_data, csv_file)
        logging.info(f"Scraping completed successfully!")
        logging.info(f"Total buses processed: {total_buses}")
        logging.info(f"Images downloaded: {successful_downloads}")
        logging.info(f"Data saved to: {csv_file}")
        logging.info(f"Images saved to: {image_dir}")
    else:
        logging.warning("No data was collected!")

if __name__ == "__main__":
    main()
