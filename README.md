# Bus Data Scraper

This project scrapes bus information from [wbbus.in/allbus](https://wbbus.in/allbus) across all pages (pages 1 to 40). It extracts comprehensive information including bus name, registration, route, stoppage times, contact details, and downloads the bus images with proper naming convention.

## Features

- **Comprehensive Data Extraction**: Extracts bus name, registration number, route information, stoppage details with up/down times, contact numbers, agency information, and more
- **Image Download**: Downloads bus images and saves them with the naming convention `BUSNAME_REGNO.extension`
- **CSV Export**: Organizes all data into a properly structured CSV file with predefined columns
- **Error Handling**: Robust error handling with retry logic for failed requests
- **Logging**: Detailed logging to both console and log file for monitoring progress
- **Rate Limiting**: Respectful delays between requests to avoid overloading the server

## Project Structure

```
/project
  ├── config.ini         # Configuration file for URLs, timeouts, paths, etc.
  ├── requirements.txt   # Required Python packages
  ├── utils.py          # Helper functions for HTTP requests, parsing, CSV writing, image downloading
  ├── scraper.py        # Main script that executes the scraping process
  ├── README.md         # This file
  ├── scraper.log       # Log file (created when script runs)
  └── output/           # Output directory (created automatically)
       ├── bus_data.csv # Extracted bus data in CSV format
       └── images/      # Downloaded bus images
```

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify configuration (optional):**
   - Check `config.ini` for any settings you want to modify
   - Default settings should work for most use cases

## Usage

Run the scraper:
```bash
python scraper.py
```

The script will:
1. Process pages 1-40 of the bus listing website
2. Extract detailed information for each bus
3. Download bus images with proper naming
4. Save all data to `output/bus_data.csv`
5. Log progress to both console and `scraper.log`

## Output Format

### CSV Columns
The generated CSV file contains the following columns:
- **Bus Name**: Name of the bus service
- **Bus Number**: Registration number (e.g., WB673279)
- **Route**: Bus route information
- **All Stoppage**: Complete list of stoppages with times
- **Stoppage Time**: Formatted stoppage timing information
- **Up Time**: Upward journey times
- **Down Time**: Downward journey times
- **AlternateName**: Alternative name for the bus service
- **Agency Name**: Operating agency name
- **Bus Type**: Type of bus (Private/Government, AC/Non-AC)
- **Contact Number**: Primary contact number
- **Alternate Number**: Secondary contact number
- **Depot Name**: Home depot of the bus
- **Destination**: Final destination

### Image Files
Bus images are saved in the `output/images/` directory with the naming convention:
```
BUSNAME_REGNO.extension
```
Example: `ANTARA_WB673279.webp`

## Configuration

The `config.ini` file contains the following settings:

```ini
[DEFAULT]
base_url = https://wbbus.in/allbus
start_page = 1
end_page = 40
csv_file = output/bus_data.csv
image_dir = output/images
timeout = 10
retry_count = 3
```

You can modify these settings as needed:
- **start_page/end_page**: Change the range of pages to scrape
- **timeout**: HTTP request timeout in seconds
- **retry_count**: Number of retry attempts for failed requests
- **csv_file/image_dir**: Change output paths

## Error Handling

The scraper includes comprehensive error handling:

- **HTTP Errors**: Automatic retry with exponential backoff
- **Parsing Errors**: Graceful handling of malformed HTML
- **Missing Data**: Empty strings used as placeholders for missing information
- **File Operations**: Automatic directory creation and file handling
- **Network Issues**: Timeout handling and connection error recovery

## Logging

The scraper provides detailed logging:
- **Console Output**: Real-time progress updates
- **Log File**: Complete log saved to `scraper.log`
- **Log Levels**: INFO for normal operations, ERROR for issues, WARNING for minor problems

## Data Cleaning

The scraper automatically cleans the extracted data:
- **Time Formatting**: Converts placeholder times ("_ _") to "00"
- **Text Normalization**: Strips whitespace and normalizes formatting
- **Filename Sanitization**: Removes invalid characters from image filenames

## Performance Considerations

- **Rate Limiting**: 2-second delay between pages, 0.5-second delay between buses
- **Memory Efficient**: Processes data incrementally rather than loading everything into memory
- **Robust Parsing**: Uses multiple parsing strategies to handle variations in HTML structure

## Troubleshooting

### Common Issues

1. **Network Timeouts**: Increase the `timeout` value in `config.ini`
2. **Missing Images**: Check if the image URLs are accessible and the `image_dir` has write permissions
3. **Empty CSV**: Verify the website structure hasn't changed and check the log file for errors
4. **Permission Errors**: Ensure the script has write permissions for the output directory

### Debugging

- Check `scraper.log` for detailed error messages
- Run with increased logging by modifying the logging level in `scraper.py`
- Test with a smaller page range by modifying `start_page` and `end_page` in `config.ini`

## Legal and Ethical Considerations

- This scraper is designed to be respectful to the target website with appropriate delays
- Always check the website's robots.txt and terms of service before scraping
- Use the scraped data responsibly and in accordance with applicable laws

## License

This project is provided as-is for educational and research purposes.
