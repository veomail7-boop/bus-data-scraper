import requests
import os
import csv
import logging
import re
from time import sleep
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def fetch_html(url, timeout=10, retry_count=3):
    """Fetch HTML content from URL with retry logic"""
    for attempt in range(retry_count):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, timeout=timeout, headers=headers)
            if response.status_code == 200:
                return response.text
            else:
                logging.error(f"Unexpected status {response.status_code} for URL: {url}")
        except Exception as e:
            logging.error(f"Error fetching URL {url} (attempt {attempt + 1}): {e}")
        if attempt < retry_count - 1:
            sleep(2)  # back-off
    return None

def parse_bus_from_card(card):
    """Parse basic bus information from bus card element"""
    data = {}
    try:
        # Extract bus name
        title_tag = card.find('h4')
        if title_tag:
            data['bus_name'] = title_tag.get_text(strip=True)
        
        # Extract registration number
        reg_text = card.get_text()
        reg_match = re.search(r'Reg No\s*:\s*([A-Z0-9]+)', reg_text)
        if reg_match:
            data['registration_number'] = reg_match.group(1)
        
        # Extract detail page URL
        href = card.get('href')
        if href:
            data['detail_url'] = urljoin('https://wbbus.in', href)
        
        # Extract image URL
        img_tag = card.find('img')
        if img_tag and img_tag.get('src'):
            data['image_url'] = urljoin('https://wbbus.in', img_tag.get('src'))
        
        # Extract route information (start and end points with times)
        text_content = card.get_text()
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        # Try to find departure and arrival info
        route_info = []
        for i, line in enumerate(lines):
            if re.search(r'\d{1,2}:\d{2}\s*(AM|PM)', line):
                route_info.append(line)
        
        if len(route_info) >= 2:
            data['departure'] = route_info[0]
            data['arrival'] = route_info[1]
        
    except Exception as e:
        logging.error(f"Error parsing bus card: {e}")
    
    return data

def parse_bus_detail(html_content):
    """Parse detailed bus information from detail page"""
    data = {}
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract all text content for pattern matching
        page_text = soup.get_text()
        
        # Extract alternate name
        alt_name_match = re.search(r'Alternate Name\s*:\s*([^\n]+)', page_text)
        if alt_name_match:
            data['alternate_name'] = alt_name_match.group(1).strip()
        
        # Extract agency name
        agency_match = re.search(r'Agency Name\s*:\s*([^\n]+)', page_text)
        if agency_match:
            data['agency_name'] = agency_match.group(1).strip()
        
        # Extract bus type
        type_match = re.search(r'Bus Type\s*:\s*([^\n]+)', page_text)
        if type_match:
            data['bus_type'] = type_match.group(1).strip()
        
        # Extract contact numbers
        contact_match = re.search(r'Contact Number\s*:\s*([0-9]+)', page_text)
        if contact_match:
            data['contact_number'] = contact_match.group(1).strip()
        
        alt_contact_match = re.search(r'Alternate Number\s*:\s*([0-9]+)', page_text)
        if alt_contact_match:
            data['alternate_number'] = alt_contact_match.group(1).strip()
        
        # Extract depot name
        depot_match = re.search(r'Depot Name\s*:\s*([^\n]+)', page_text)
        if depot_match:
            data['depot_name'] = depot_match.group(1).strip()
        
        # Extract destination
        dest_match = re.search(r'Destination\s*:\s*([^\n]+)', page_text)
        if dest_match:
            data['destination'] = dest_match.group(1).strip()
        
        # Extract stoppage information
        stoppage_data = extract_stoppage_info(soup)
        data.update(stoppage_data)
        
        # Extract bus notes
        notes_section = soup.find(text=re.compile(r'Bus Notes'))
        if notes_section:
            notes_parent = notes_section.parent
            if notes_parent:
                notes_text = notes_parent.get_text()
                data['bus_notes'] = notes_text.strip()
        
    except Exception as e:
        logging.error(f"Error parsing bus detail: {e}")
    
    return data

def extract_stoppage_info(soup):
    """Extract stoppage information with up/down times"""
    stoppage_data = {}
    try:
        # Look for stoppage information in various formats
        page_text = soup.get_text()
        
        # Find all stoppage entries with times
        stoppage_pattern = r'([A-Za-z\s]+),?\s*Uptime[-\s]*(\d{1,2}:\d{2}\s*[AP]M|\d{2}|_\s*_),?\s*DownTime[-\s]*(\d{1,2}:\d{2}\s*[AP]M|\d{2}|_\s*_)'
        matches = re.findall(stoppage_pattern, page_text, re.IGNORECASE)
        
        all_stoppages = []
        up_times = []
        down_times = []
        
        for match in matches:
            stoppage_name = match[0].strip()
            up_time = clean_time_string(match[1])
            down_time = clean_time_string(match[2])
            
            all_stoppages.append(f"{stoppage_name}, Uptime- {up_time}, DownTime- {down_time}")
            up_times.append(up_time)
            down_times.append(down_time)
        
        if all_stoppages:
            stoppage_data['all_stoppage'] = "; ".join(all_stoppages)
            stoppage_data['up_time'] = ", ".join(up_times)
            stoppage_data['down_time'] = ", ".join(down_times)
        
        # Extract route information
        route_match = re.search(r'([A-Z\s]+)\s*-\s*([A-Z\s]+)', page_text)
        if route_match:
            stoppage_data['route'] = f"{route_match.group(1).strip()} - {route_match.group(2).strip()}"
        
    except Exception as e:
        logging.error(f"Error extracting stoppage info: {e}")
    
    return stoppage_data

def download_image(url, save_path):
    """Download image from URL and save to specified path"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, stream=True, headers=headers, timeout=10)
        if response.status_code == 200:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as out_file:
                for chunk in response.iter_content(1024):
                    out_file.write(chunk)
            logging.info(f"Downloaded image: {save_path}")
            return True
        else:
            logging.error(f"Failed to download image {url}: Status {response.status_code}")
    except Exception as e:
        logging.error(f"Error downloading image {url}: {e}")
    return False

def write_csv(data_rows, csv_file):
    """Write data rows to CSV file"""
    headers = [
        'Bus Name', 'Bus Number', 'Route', 'All Stoppage', 'Stoppage Time',
        'Up Time', 'Down Time', 'AlternateName', 'Agency Name', 'Bus Type',
        'Contact Number', 'Alternate Number', 'Depot Name', 'Destination'
    ]
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in data_rows:
                writer.writerow(row)
        logging.info(f"CSV file written successfully: {csv_file}")
    except Exception as e:
        logging.error(f"Error writing CSV file: {e}")

def clean_time_string(time_str):
    """Clean time string, replacing placeholders with '00'"""
    if not time_str or time_str.strip() == '':
        return '00'
    
    # Replace underscores and dashes with '00'
    cleaned = re.sub(r'[_\-\s]+', '00', time_str.strip())
    
    # If it's just '00' or similar, return '00'
    if re.match(r'^[_\-\s0]*$', cleaned):
        return '00'
    
    return cleaned

def sanitize_filename(filename):
    """Sanitize filename by removing invalid characters"""
    # Remove invalid characters for filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove extra spaces and replace with underscores
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized
