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

    def fetch(self) -> BeautifulSoup:
        response = requests.get(self.url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

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
                    "scraped_at": datetime.now(timezone.utc).isoformat()
                })

            except Exception:
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

    def _fetch_uk_detail(self, url: str) -> Dict[str, str]:
        """Fetch UK country detail page and extract summary/risk hints."""
        headers = {"User-Agent": self.get_random_user_agent()}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "lxml")

            # Gov.uk pages usually keep rich advisory text in this container.
            content = soup.select_one("main #content") or soup.select_one("main")
            if not content:
                return {"risk_level": "Unknown", "description": ""}

            # Keep first few meaningful paragraphs for analyzer context.
            paras = []
            for p in content.find_all("p"):
                txt = p.get_text(" ", strip=True)
                if txt and len(txt) > 40:
                    paras.append(txt)
                if len(paras) >= 4:
                    break

            full_text = content.get_text(" ", strip=True)
            risk = self._extract_uk_risk_level(full_text)
            description = " ".join(paras).strip()
            return {"risk_level": risk, "description": description}
        except Exception:
            return {"risk_level": "Unknown", "description": ""}
    
    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        advisories = []
        
        try:
            # UK gov.uk structure - find country links/entries
            country_links = soup.find_all('a', href=re.compile(r'/foreign-travel-advice/'))
            seen_urls = set()
            max_rows = int(os.getenv("FCDO_MAX_ROWS", "80"))

            for link in country_links:
                try:
                    country = link.get_text(strip=True)
                    url = link.get('href', '')
                    if not url.startswith('http'):
                        url = f"https://www.gov.uk{url}"

                    # Ignore duplicates and non-country helper links.
                    slug = url.rstrip("/").split("/")[-1].lower()
                    if (
                        not country
                        or country.lower().startswith("get email alerts")
                        or slug in {"foreign-travel-advice", "travel-advice-help", "email-signup"}
                        or url in seen_urls
                    ):
                        continue
                    seen_urls.add(url)

                    detail = self._fetch_uk_detail(url)
                    risk_level = detail.get("risk_level", "Unknown")
                    description = detail.get("description", "")

                    # Keep only meaningful advisories for downstream insights.
                    if (not description or len(description.strip()) < 40) and risk_level == "Unknown":
                        continue

                    advisories.append({
                        'source': 'UK FCDO',
                        'country': country,
                        'risk_level': risk_level,
                        'date': None,
                        'description': description,
                        'url': url,
                        'scraped_at': datetime.now().isoformat()
                    })

                    if len(advisories) >= max_rows:
                        break
                    time.sleep(0.05)
                except Exception as e:
                    print(f"Error parsing UK FCDO item: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing UK FCDO page: {e}")
        
        return advisories


# ==========================================================
# SMART TRAVELLER (AUSTRALIA)
# ==========================================================

class SmartTravellerScraper(BaseScraper):
    """Scraper for Australian Smart Traveller"""

    def fetch(self) -> BeautifulSoup:
        response = requests.get(self.url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        advisories = []

        links = soup.find_all("a", href=re.compile(r"/destinations/"))

        for link in links:
            try:
                country = link.get_text(strip=True)
                url = link["href"]

                if not url.startswith("http"):
                    url = f"https://www.smartraveller.gov.au{url}"

                advisories.append({
                    "source": "Smart Traveller (Australia)",
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
# CANADA TRAVEL
# ==========================================================

class CanadaTravelScraper(BaseScraper):
    """Scraper for Canada Travel Advisories"""

    def fetch(self) -> BeautifulSoup:
        response = requests.get(self.url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        advisories = []

        links = soup.find_all("a", href=re.compile(r"/destinations/"))

        for link in links:
            try:
                country = link.get_text(strip=True)
                url = link["href"]

                if not url.startswith("http"):
                    url = f"https://travel.gc.ca{url}"

                advisories.append({
                    "source": "Canada Travel",
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
