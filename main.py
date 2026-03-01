"""
Main Orchestration Script for Travel Advisory Scraper
"""
import os
import time
import schedule
from typing import List, Dict

from tqdm import tqdm

import config
from proxy_manager import ProxyManager
from scrapers import (
    USStateDeptScraper,
    UKFCDOScraper,
    SmartTravellerScraper,
    IATAScraper,
    CanadaTravelScraper,
)
from db_factory import get_handler
from data_cleaner import DataCleaner


class TravelAdvisoryPipeline:
    """Main pipeline for scraping, cleaning, and storing travel advisories"""

    def __init__(self):
        self.proxy_manager = None
        if config.PROXY_CONFIG["proxies"]:
            self.proxy_manager = ProxyManager(
                proxies=config.PROXY_CONFIG["proxies"],
                rotation_strategy=config.PROXY_CONFIG["rotation_strategy"],
            )
            print(f"Proxy manager initialized with {len(config.PROXY_CONFIG['proxies'])} proxies")
        else:
            print("Warning: No proxies configured. Running without proxy rotation.")

        self.db = get_handler()
        self.cleaner = DataCleaner()

        self.scrapers = {
            "us_state_dept": (USStateDeptScraper, config.TARGET_URLS["us_state_dept"]),
            "uk_fcdo": (UKFCDOScraper, config.TARGET_URLS["uk_fcdo"]),
            "smartraveller": (SmartTravellerScraper, config.TARGET_URLS["smartraveller"]),
            "iata": (IATAScraper, config.TARGET_URLS["iata"]),
            "canada": (CanadaTravelScraper, config.TARGET_URLS["canada"]),
        }

    def scrape_all(self) -> List[Dict]:
        """Scrape all configured sources."""
        all_advisories = []
        use_playwright = os.getenv("USE_PLAYWRIGHT", "false").strip().lower() in {"1", "true", "yes"}

        print("\n" + "=" * 60)
        print("Starting Scraping Process")
        print("=" * 60)

        for source_name, (scraper_class, url) in tqdm(self.scrapers.items(), desc="Scraping sources"):
            print(f"\nScraping {source_name}...")
            try:
                scraper = scraper_class(
                    url=url,
                    proxy_manager=self.proxy_manager,
                    use_playwright=use_playwright,
                )
                advisories = scraper.scrape()

                if advisories:
                    print(f"  + Found {len(advisories)} advisories from {source_name}")
                    all_advisories.extend(advisories)
                else:
                    print(f"  - No advisories found from {source_name}")

                scraper.close()
                time.sleep(1.5)
            except Exception as e:
                print(f"  - Error scraping {source_name}: {e}")
                continue

        print(f"\nTotal advisories scraped: {len(all_advisories)}")
        return all_advisories

    def clean_data(self, advisories: List[Dict]) -> List[Dict]:
        """Clean and normalize scraped data."""
        print("\n" + "=" * 60)
        print("Cleaning Data")
        print("=" * 60)

        cleaned = self.cleaner.clean_batch(advisories)
        deduplicated = self.cleaner.deduplicate(cleaned)
        quality_filtered = []

        for adv in deduplicated:
            country_ok = (adv.get("country_normalized") or adv.get("country") or "").strip().lower() != "unknown"
            risk_ok = (adv.get("risk_score") or 0) > 0
            desc = (adv.get("description_cleaned") or adv.get("description") or "").strip()
            text_ok = len(desc) >= 40
            if country_ok and (risk_ok or text_ok):
                quality_filtered.append(adv)

        print(f"Cleaned {len(cleaned)} advisories")
        print(f"After deduplication: {len(deduplicated)} advisories")
        print(f"After quality filter: {len(quality_filtered)} advisories")
        return quality_filtered

    def store_data(self, advisories: List[Dict]):
        """Store cleaned data in database."""
        print("\n" + "=" * 60)
        print("Storing Data in Database")
        print("=" * 60)
        inserted_count = self.db.insert_advisories(advisories)
        print(f"Inserted/Updated {inserted_count} advisories in the database.")

    def run_full_pipeline(self):
        """Run the complete pipeline."""
        print("\n" + "=" * 60)
        print("TRAVEL ADVISORY SCRAPER PIPELINE")
        print("=" * 60)
        try:
            advisories = self.scrape_all()
            if not advisories:
                print("No advisories scraped. Exiting.")
                return

            cleaned_advisories = self.clean_data(advisories)
            self.store_data(cleaned_advisories)

            print("\n" + "=" * 60)
            print("Pipeline completed successfully!")
            print("=" * 60)
        except Exception as e:
            print(f"\nError in pipeline: {e}")
            raise
        finally:
            self.db.close()

    def run_scheduled(self, interval_hours: int = 6):
        """Run pipeline on a schedule."""
        print(f"Scheduling pipeline to run every {interval_hours} hours")
        schedule.every(interval_hours).hours.do(self.run_full_pipeline)
        self.run_full_pipeline()
        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Travel Advisory Scraper")
    parser.add_argument(
        "--schedule",
        type=int,
        default=0,
        help="Run on schedule (interval in hours, 0 = run once)",
    )
    args = parser.parse_args()

    pipeline = TravelAdvisoryPipeline()
    if args.schedule > 0:
        pipeline.run_scheduled(interval_hours=args.schedule)
    else:
        pipeline.run_full_pipeline()


if __name__ == "__main__":
    main()
