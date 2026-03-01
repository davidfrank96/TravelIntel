"""
Production Base Scraper
Reusable session + retries + logging
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import config


logger = logging.getLogger(__name__)


class BaseScraper(ABC):

    def __init__(self, url: str):
        self.url = url
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()

        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            "User-Agent": "TravelIntelBot/1.0",
            "Accept": "text/html",
        })

        return session

    def fetch(self) -> Optional[BeautifulSoup]:
        try:
            response = self.session.get(
                self.url,
                timeout=config.SCRAPER_CONFIG["timeout"],
            )
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")

        except Exception as e:
            logger.error(f"Failed fetching {self.url}: {e}")
            return None

    @abstractmethod
    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        pass

    def scrape(self) -> List[Dict]:
        soup = self.fetch()
        if soup:
            return self.parse(soup)
        return []
