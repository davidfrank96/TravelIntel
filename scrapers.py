"""
Individual Scrapers for Each Travel Advisory Site
"""
import re
import time
import os
from datetime import datetime
from typing import List, Dict
from bs4 import BeautifulSoup
import requests
from scraper_base import BaseScraper
import config


class USStateDeptScraper(BaseScraper):
    """Scraper for U.S. Department of State Travel Advisories"""
    
    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse US State Department travel advisories"""
        advisories = []
        
        try:
            # Find advisory entries - structure may vary, adjust selectors as needed
            advisory_items = soup.find_all(['div', 'article', 'li'], 
                                          class_=re.compile(r'advisory|travel|warning', re.I))
            
            for item in advisory_items:
                try:
                    # Extract country name
                    country_elem = item.find(['h2', 'h3', 'h4', 'a'], 
                                            class_=re.compile(r'country|title', re.I))
                    country = country_elem.get_text(strip=True) if country_elem else 'Unknown'
                    
                    # Extract risk level
                    risk_elem = item.find(['span', 'div'], 
                                         class_=re.compile(r'level|risk|advisory', re.I))
                    risk_level = risk_elem.get_text(strip=True) if risk_elem else 'Unknown'
                    
                    # Extract date
                    date_elem = item.find(['time', 'span'], 
                                         class_=re.compile(r'date|updated', re.I))
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True) if date_elem else None
                    
                    # Extract summary/description (grab multiple paragraphs if available)
                    desc_elem = item.find(['p', 'div'], 
                                         class_=re.compile(r'description|summary|content', re.I))
                    if desc_elem:
                        paragraphs = desc_elem.find_all('p') or [desc_elem]
                        description = ' '.join(p.get_text(" ", strip=True) for p in paragraphs)
                    else:
                        # fallback: any <p> tags under the item
                        paragraphs = item.find_all('p')
                        description = ' '.join(p.get_text(" ", strip=True) for p in paragraphs[:4])
                    
                    # Extract link
                    link_elem = item.find('a', href=True)
                    link = link_elem['href'] if link_elem else None
                    if link and not link.startswith('http'):
                        link = f"https://travel.state.gov{link}"
                    
                    advisories.append({
                        'source': 'US State Department',
                        'country': country,
                        'risk_level': risk_level,
                        'date': date_str,
                        'description': description,
                        'url': link or self.url,
                        'scraped_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"Error parsing advisory item: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing US State Department page: {e}")
        
        return advisories


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
        """Parse UK FCDO travel advice"""
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


class SmartTravellerScraper(BaseScraper):
    """Scraper for Australian Smart Traveller"""
    
    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse Smart Traveller advisories"""
        advisories = []
        
        try:
            # Find destination entries
            destinations = soup.find_all(['div', 'article', 'li'], 
                                       class_=re.compile(r'destination|country|advisory', re.I))
            
            for dest in destinations:
                try:
                    # Extract country
                    country_elem = dest.find(['h2', 'h3', 'a'], 
                                           class_=re.compile(r'title|name|country', re.I))
                    country = country_elem.get_text(strip=True) if country_elem else 'Unknown'
                    
                    # Extract advice level
                    level_elem = dest.find(['span', 'div'], 
                                         class_=re.compile(r'level|advice|risk', re.I))
                    risk_level = level_elem.get_text(strip=True) if level_elem else 'Unknown'
                    
                    # Extract some descriptive text
                    desc_elem = dest.find(['div', 'p'], 
                                          class_=re.compile(r'summary|description|content', re.I))
                    if desc_elem:
                        paragraphs = desc_elem.find_all('p') or [desc_elem]
                        description = ' '.join(p.get_text(" ", strip=True) for p in paragraphs[:4])
                    else:
                        paragraphs = dest.find_all('p')
                        description = ' '.join(p.get_text(" ", strip=True) for p in paragraphs[:4])
                    
                    # Extract link
                    link_elem = dest.find('a', href=True)
                    link = link_elem['href'] if link_elem else None
                    if link and not link.startswith('http'):
                        link = f"https://www.smartraveller.gov.au{link}"
                    
                    advisories.append({
                        'source': 'Smart Traveller (Australia)',
                        'country': country,
                        'risk_level': risk_level,
                        'date': None,
                        'description': description,
                        'url': link or self.url,
                        'scraped_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"Error parsing Smart Traveller item: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing Smart Traveller page: {e}")
        
        return advisories


class IATAScraper(BaseScraper):
    """Scraper for IATA Travel Centre"""
    
    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse IATA travel centre information"""
        advisories = []
        
        try:
            # IATA structure - find country entries
            country_entries = soup.find_all(['div', 'tr', 'li'], 
                                          class_=re.compile(r'country|destination', re.I))
            
            for entry in country_entries:
                try:
                    # Extract country name
                    country_elem = entry.find(['a', 'td', 'span'], 
                                            class_=re.compile(r'country|name', re.I))
                    country = country_elem.get_text(strip=True) if country_elem else 'Unknown'
                    
                    # Extract restrictions/requirements
                    restrictions_elem = entry.find(['div', 'td', 'span'], 
                                                  class_=re.compile(r'restriction|requirement|info', re.I))
                    description = restrictions_elem.get_text(strip=True) if restrictions_elem else ''
                    
                    # Extract link
                    link_elem = entry.find('a', href=True)
                    link = link_elem['href'] if link_elem else None
                    if link and not link.startswith('http'):
                        link = f"https://www.iatatravelcentre.com{link}"
                    
                    advisories.append({
                        'source': 'IATA Travel Centre',
                        'country': country,
                        'risk_level': 'Information',
                        'date': None,
                        'description': description,
                        'url': link or self.url,
                        'scraped_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"Error parsing IATA item: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing IATA page: {e}")
        
        return advisories


class CanadaTravelScraper(BaseScraper):
    """Scraper for Canada Travel Advisories"""
    
    def parse(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse Canada travel advisories"""
        advisories = []
        
        try:
            # Find advisory entries
            advisory_items = soup.find_all(['div', 'article', 'li'], 
                                         class_=re.compile(r'advisory|travel|warning', re.I))
            
            for item in advisory_items:
                try:
                    country_elem = item.find(['h2', 'h3', 'a'], 
                                           class_=re.compile(r'country|title', re.I))
                    country = country_elem.get_text(strip=True) if country_elem else 'Unknown'
                    
                    risk_elem = item.find(['span', 'div'], 
                                         class_=re.compile(r'level|risk|advisory', re.I))
                    risk_level = risk_elem.get_text(strip=True) if risk_elem else 'Unknown'
                    
                    # Pull descriptive paragraphs
                    desc_elem = item.find(['div', 'p'], 
                                          class_=re.compile(r'summary|description|content', re.I))
                    if desc_elem:
                        paragraphs = desc_elem.find_all('p') or [desc_elem]
                        description = ' '.join(p.get_text(" ", strip=True) for p in paragraphs[:4])
                    else:
                        paragraphs = item.find_all('p')
                        description = ' '.join(p.get_text(" ", strip=True) for p in paragraphs[:4])
                    
                    link_elem = item.find('a', href=True)
                    link = link_elem['href'] if link_elem else None
                    if link and not link.startswith('http'):
                        link = f"https://travel.gc.ca{link}"
                    
                    advisories.append({
                        'source': 'Canada Travel',
                        'country': country,
                        'risk_level': risk_level,
                        'date': None,
                        'description': description,
                        'url': link or self.url,
                        'scraped_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"Error parsing Canada Travel item: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing Canada Travel page: {e}")
        
        return advisories
