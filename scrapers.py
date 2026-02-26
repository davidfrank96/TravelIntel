"""
scrappers.py
Individual Scrapers for Each Travel Advisory Site
HTTP-based scraping (No Playwright)
"""

import re
import requests
from datetime import datetime, timezone
from typing import List, Dict
from bs4 import BeautifulSoup
from scraper_base import BaseScraper


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TravelIntelBot/1.0)"
}


# ==========================================================
# US STATE DEPARTMENT
# ==========================================================

class USStateDeptScraper(BaseScraper):
    """Scraper for U.S. Department of State Travel Advisories"""

    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        advisories = []

        advisory_items = soup.find_all("a", href=re.compile(r"/traveladvisories/"))

        for item in advisory_items:
            try:
                country = item.get_text(strip=True)
                link = item["href"]

                if not link.startswith("http"):
                    link = f"https://travel.state.gov{link}"

                advisories.append({
                    "source": "US State Department",
                    "country": country,
                    "risk_level": "See advisory page",
                    "date": None,
                    "description": "",
                    "url": link,
                    "scraped_at": datetime.utcnow().isoformat()
                })

            except Exception as e:
                logger.warning(f"Skipping item: {e}")
                continue

        return advisories

# ==========================================================
# UK FCDO
# ==========================================================

class UKFCDOScraper(BaseScraper):
    """Scraper for UK Foreign Travel Advice"""

    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        advisories = []

        advisory_items = soup.find_all("a", href=re.compile(r"/traveladvisories/"))

        for item in advisory_items:
            try:
                country = item.get_text(strip=True)
                link = item["href"]

                if not link.startswith("http"):
                    link = f"https://travel.state.gov{link}"

                advisories.append({
                    "source": "UK Foreign Travel",
                    "country": country,
                    "risk_level": "See advisory page",
                    "date": None,
                    "description": "",
                    "url": link,
                    "scraped_at": datetime.utcnow().isoformat()
                })

            except Exception as e:
                logger.warning(f"Skipping item: {e}")
                continue

        return advisories


# ==========================================================
# SMART TRAVELLER (AUSTRALIA)
# ==========================================================

class SmartTravellerScraper(BaseScraper):
    """Scraper for Australian Smart Traveller"""
    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        advisories = []

        advisory_items = soup.find_all("a", href=re.compile(r"/traveladvisories/"))

        for item in advisory_items:
            try:
                country = item.get_text(strip=True)
                link = item["href"]

                if not link.startswith("http"):
                    link = f"https://travel.state.gov{link}"

                advisories.append({
                    "source": "Smart Traveller",
                    "country": country,
                    "risk_level": "See advisory page",
                    "date": None,
                    "description": "",
                    "url": link,
                    "scraped_at": datetime.utcnow().isoformat()
                })

            except Exception as e:
                logger.warning(f"Skipping item: {e}")
                continue

        return advisories


# ==========================================================
# CANADA TRAVEL
# ==========================================================

class CanadaTravelScraper(BaseScraper):
    """Scraper for Canada Travel Advisories"""
    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        advisories = []

        advisory_items = soup.find_all("a", href=re.compile(r"/traveladvisories/"))

        for item in advisory_items:
            try:
                country = item.get_text(strip=True)
                link = item["href"]

                if not link.startswith("http"):
                    link = f"https://travel.state.gov{link}"

                advisories.append({
                    "source": "Canada Travel",
                    "country": country,
                    "risk_level": "See advisory page",
                    "date": None,
                    "description": "",
                    "url": link,
                    "scraped_at": datetime.utcnow().isoformat()
                })

            except Exception as e:
                logger.warning(f"Skipping item: {e}")
                continue

        return advisories

