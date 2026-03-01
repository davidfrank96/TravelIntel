"""
scrappers.py
Individual Scrapers for Each Travel Advisory Site
HTTP-based scraping (No Playwright)
"""

import re
import time
import os
from datetime import datetime
from typing import List, Dict
from bs4 import BeautifulSoup
import requests
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
    """Scraper for UK Foreign, Commonwealth & Development Office"""

    def _extract_uk_risk_level(self, text: str) -> str:
        """Infer UK advisory level from detail page text."""
        low = (text or "").lower()
        if "advises against all travel" in low:
            return "Advise Against All Travel"
        if "advises against all but essential travel" in low:
            return "Advise Against All But Essential Travel"
        if "see our travel advice" in low:
            return "See Official Advice"
        return "Unknown"

    def fetch(self) -> BeautifulSoup:
        response = requests.get(self.url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        advisories = []

        country_links = soup.find_all("a", href=re.compile(r"/foreign-travel-advice/"))

        for link in country_links:
            try:
                country = link.get_text(strip=True)
                url = link["href"]

                if not url.startswith("http"):
                    url = f"https://www.gov.uk{url}"

                advisories.append({
                    "source": "UK FCDO",
                    "country": country,
                    "risk_level": "See advisory page",
                    "date": None,
                    "description": "",
                    "url": url,
                    "scraped_at": datetime.now(timezone.utc).isoformat()
                })

            except Exception:
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

