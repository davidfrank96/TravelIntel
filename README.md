# Travel Advisory Scraper with AI Prediction

A comprehensive web scraping system for collecting travel advisories from multiple government sources, with data cleaning, PostgreSQL storage, and AI-powered risk prediction.

## Features

- **Rotating Residential Proxy Support**: Built-in proxy rotation manager for reliable scraping
- **Multiple Scraping Engines**: Supports Playwright, Selenium, and Requests
- **Multiple Data Sources**:
  - U.S. Department of State (travel.state.gov)
  - UK Foreign Office (FCDO) (gov.uk/foreign-travel-advice)
  - Australian Smart Traveller (smartraveller.gov.au)
  - IATA Travel Centre (iatatravelcentre.com)
  - Canada Travel Advisories (travel.gc.ca)
- **Data Cleaning & Normalization**: Automatic country name and risk level normalization
- **PostgreSQL Database**: Structured storage with proper indexing
- **AI Prediction**: Machine learning model for risk level prediction
- **Scheduled Scraping**: Automated periodic data collection

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers** (if using Playwright):
```bash
playwright install chromium
```

4. **Install ChromeDriver** (if using Selenium):
   - Download from https://chromedriver.chromium.org/
   - Add to PATH or specify in code

5. **Set up PostgreSQL database**:
```sql
CREATE DATABASE travel_advisories;
```

6. **Configure environment variables**:
   - Copy `.env.example` to `.env`
   - Update database credentials
   - Add your proxy credentials (if using proxies)

7. **Configure proxies** (optional):
   Edit `config.py` and add your proxy URLs to `PROXY_CONFIG['proxies']`:
```python
'proxies': [
    'http://username:password@proxy1.example.com:8080',
    'http://username:password@proxy2.example.com:8080',
]
```

## Usage

### Basic Usage

Run the scraper once:
```bash
python main.py
```

### Scheduled Scraping

Run every 6 hours:
```bash
python main.py --schedule 6
```

### Scrape Specific Source

```bash
python main.py --source us_state_dept
```

### Run the Dashboard UI

After you have scraped some data and the database has records:

```bash
streamlit run dashboard.py
```

This opens a web UI where users can explore security, safety, and serenity
insights per country (no predictions, only descriptive analysis).

## Project Structure

```
OSINT/
├── main.py                 # Main orchestration script
├── config.py              # Configuration settings
├── proxy_manager.py       # Proxy rotation manager
├── scraper_base.py        # Base scraper class
├── scrapers.py            # Individual site scrapers
├── database.py            # PostgreSQL database handler
├── data_cleaner.py        # Data cleaning and normalization
├── ai_predictor.py        # AI prediction module
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Configuration

### Database Configuration

Edit `config.py` or set environment variables:
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: travel_advisories)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password

### Proxy Configuration

Add your residential proxy credentials to `config.py`:
```python
PROXY_CONFIG = {
    'proxies': [
        'http://user:pass@proxy1.example.com:8080',
        # Add more proxies...
    ],
    'rotation_strategy': 'round_robin',  # or 'random', 'least_used'
    'timeout': 30,
    'max_retries': 3
}
```

### Scraper Configuration

Adjust scraping behavior in `config.py`:
```python
SCRAPER_CONFIG = {
    'headless': True,        # Run browser in headless mode
    'timeout': 30000,        # Page load timeout (ms)
    'wait_time': 3,          # Wait time after page load (seconds)
    'user_agent_rotation': True,
    'respect_robots_txt': False
}
```

## Database Schema

### travel_advisories
- `id`: Primary key
- `source`: Source website
- `country`: Country name
- `risk_level`: Risk level text
- `date`: Advisory date
- `description`: Full description
- `url`: Source URL
- `scraped_at`: Scraping timestamp

### processed_advisories
- `id`: Primary key
- `advisory_id`: Foreign key to travel_advisories
- `country_normalized`: Normalized country name
- `risk_level_normalized`: Normalized risk level
- `risk_score`: Numeric risk score (1-4)
- `keywords`: Extracted keywords array
- `sentiment_score`: Sentiment analysis score

### predictions
- `id`: Primary key
- `advisory_id`: Foreign key to travel_advisories
- `predicted_risk_level`: AI predicted risk level
- `predicted_risk_score`: AI predicted score
- `confidence`: Prediction confidence
- `model_version`: Model version used

## Data Cleaning

The `DataCleaner` class provides:
- Country name normalization
- Risk level standardization
- Risk score extraction (1-4 scale)
- Keyword extraction
- Text cleaning
- Deduplication

## AI Prediction

The `AIPredictor` class uses:
- Random Forest Classifier
- TF-IDF vectorization for text features
- Automatic model training on historical data
- Risk level prediction with confidence scores

## Customization

### Adding New Scrapers

1. Create a new scraper class inheriting from `BaseScraper`:
```python
class NewSourceScraper(BaseScraper):
    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        # Implement parsing logic
        return advisories
```

2. Add to `scrapers.py` and register in `main.py`

### Modifying Parsing Logic

Each scraper's `parse()` method can be customized based on the website structure. You may need to inspect the HTML structure of target sites and adjust selectors accordingly.

## Troubleshooting

### Proxy Issues
- Verify proxy credentials are correct
- Check proxy format: `http://user:pass@host:port`
- Test proxies manually before running scraper

### Database Connection Issues
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists

### Scraping Failures
- Some sites may have changed structure - update selectors in scrapers
- Increase timeout values if pages load slowly
- Check if sites require JavaScript rendering (use Playwright/Selenium)

### Model Training Issues
- Ensure sufficient historical data exists
- Check that risk levels are properly normalized
- Verify feature extraction is working

## Legal & Ethical Considerations

- Respect website terms of service
- Implement rate limiting
- Consider robots.txt compliance
- Use proxies responsibly
- Only scrape publicly available data

## License

This project is provided as-is for educational and research purposes.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review configuration settings
3. Inspect error messages for specific issues
