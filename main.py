"""
Main Orchestration Script for Travel Advisory Scraper
"""
import os
import time
import schedule
import threading
import json
from typing import List, Dict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

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

        self.cleaner = DataCleaner()
        self.db = None
        self.health_state = {
            "status": "idle",
            "last_run_started_at": None,
            "last_run_finished_at": None,
            "last_scraped_count": 0,
            "last_stored_count": 0,
            "last_error": "",
        }
        self._health_server = None
        self._health_thread = None

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
        if self.db is None:
            raise RuntimeError("Database connection not initialized.")
        inserted_count = self.db.insert_advisories(advisories)
        print(f"Inserted/Updated {inserted_count} advisories in the database.")
        self.health_state["last_stored_count"] = int(inserted_count)

    def _ensure_db(self):
        if self.db is None:
            self.db = get_handler()

    def _close_db(self):
        if self.db is not None:
            self.db.close()
            self.db = None

    def _start_health_server(self, port: int):
        """Expose lightweight health endpoint for container healthchecks."""
        if self._health_server is not None:
            return

        pipeline = self

        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path not in {"/health", "/healthz"}:
                    self.send_response(404)
                    self.end_headers()
                    return
                state = dict(pipeline.health_state)
                code = 200 if state.get("status") in {"idle", "running", "ok"} else 503
                body = json.dumps(state).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt, *args):
                return

        self._health_server = HTTPServer(("0.0.0.0", port), HealthHandler)
        self._health_thread = threading.Thread(target=self._health_server.serve_forever, daemon=True)
        self._health_thread.start()
        print(f"Scraper health endpoint running on :{port}/healthz")

    def run_full_pipeline(self):
        """Run the complete pipeline."""
        print("\n" + "=" * 60)
        print("TRAVEL ADVISORY SCRAPER PIPELINE")
        print("=" * 60)
        try:
            self.health_state["status"] = "running"
            self.health_state["last_run_started_at"] = datetime.utcnow().isoformat()
            self.health_state["last_error"] = ""
            self.health_state["last_scraped_count"] = 0
            self.health_state["last_stored_count"] = 0
            self._ensure_db()

            advisories = self.scrape_all()
            self.health_state["last_scraped_count"] = int(len(advisories))
            if not advisories:
                print("No advisories scraped. Exiting.")
                self.health_state["status"] = "ok"
                self.health_state["last_run_finished_at"] = datetime.utcnow().isoformat()
                return

            cleaned_advisories = self.clean_data(advisories)
            self.store_data(cleaned_advisories)

            print("\n" + "=" * 60)
            print("Pipeline completed successfully!")
            print("=" * 60)
            self.health_state["status"] = "ok"
            self.health_state["last_run_finished_at"] = datetime.utcnow().isoformat()
        except Exception as e:
            print(f"\nError in pipeline: {e}")
            self.health_state["status"] = "error"
            self.health_state["last_error"] = str(e)
            self.health_state["last_run_finished_at"] = datetime.utcnow().isoformat()
            raise
        finally:
            self._close_db()

    def run_scheduled(self, interval_hours: int = 6):
        """Run pipeline on a schedule."""
        print(f"Scheduling pipeline to run every {interval_hours} hours")
        health_port = int(os.getenv("SCRAPER_HEALTH_PORT", "8081"))
        self._start_health_server(health_port)
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
    parser.add_argument(
        "--health-port",
        type=int,
        default=int(os.getenv("SCRAPER_HEALTH_PORT", "8081")),
        help="Scraper health endpoint port",
    )
    args = parser.parse_args()
    os.environ["SCRAPER_HEALTH_PORT"] = str(args.health_port)

    pipeline = TravelAdvisoryPipeline()
    if args.schedule <= 0:
        pipeline._start_health_server(args.health_port)
    if args.schedule > 0:
        pipeline.run_scheduled(interval_hours=args.schedule)
    else:
        pipeline.run_full_pipeline()


if __name__ == "__main__":
    main()
