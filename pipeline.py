"""
Production Travel Advisory Pipeline
Designed for DigitalOcean Worker + PostgreSQL
"""

import os
import logging
import time
from typing import List, Dict
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor

from scrapers import (
    USStateDeptScraper,
    UKFCDOScraper,
    SmartTravellerScraper,
    CanadaTravelScraper,
)
from data_cleaner import DataCleaner
import config


# -------------------------------------------------
# LOGGING CONFIG
# -------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# -------------------------------------------------
# DATABASE
# -------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")


@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# -------------------------------------------------
# PIPELINE
# -------------------------------------------------

class TravelAdvisoryPipeline:

    def __init__(self):
        self.cleaner = DataCleaner()

        self.scrapers = {
            "us_state_dept": (
                USStateDeptScraper,
                config.TARGET_URLS["us_state_dept"],
            ),
            "uk_fcdo": (
                UKFCDOScraper,
                config.TARGET_URLS["uk_fcdo"],
            ),
            "smart_traveller": (
                SmartTravellerScraper,
                config.TARGET_URLS["smart_traveller"],
            ),
            "canada_travel": (
                CanadaTravelScraper,
                config.TARGET_URLS["canada_travel"],
            ),
        }

    # ---------------------------------------------
    # SCRAPING
    # ---------------------------------------------

    def scrape_all(self) -> List[Dict]:
        all_advisories = []

        for source_name, (scraper_class, url) in self.scrapers.items():
            logger.info(f"Scraping {source_name}...")

            try:
                scraper = scraper_class(url=url)
                results = scraper.scrape()

                if results:
                    logger.info(f"{source_name}: {len(results)} advisories")
                    all_advisories.extend(results)
                else:
                    logger.warning(f"{source_name}: No advisories found")

                time.sleep(2)  # polite rate limiting

            except Exception as e:
                logger.error(f"{source_name} failed: {e}", exc_info=True)

        logger.info(f"Total scraped: {len(all_advisories)}")
        return all_advisories

    # ---------------------------------------------
    # CLEANING
    # ---------------------------------------------

    def clean(self, advisories: List[Dict]) -> List[Dict]:
        logger.info("Cleaning data...")

        cleaned = self.cleaner.clean_batch(advisories)
        deduped = self.cleaner.deduplicate(cleaned)

        logger.info(
            f"Cleaned: {len(cleaned)} | After dedupe: {len(deduped)}"
        )

        return deduped

    # ---------------------------------------------
    # STORAGE
    # ---------------------------------------------

    def store(self, advisories: List[Dict]) -> int:
        logger.info("Storing advisories in PostgreSQL...")

        if not advisories:
            return 0

        insert_query = """
            INSERT INTO advisories (
                source,
                country_normalized,
                risk_level_normalized,
                risk_score,
                sentiment_score,
                url,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (source, country_normalized)
            DO UPDATE SET
                risk_level_normalized = EXCLUDED.risk_level_normalized,
                risk_score = EXCLUDED.risk_score,
                sentiment_score = EXCLUDED.sentiment_score,
                url = EXCLUDED.url,
                created_at = NOW();
        """

        rows = [
            (
                item.get("source"),
                item.get("country_normalized"),
                item.get("risk_level_normalized"),
                item.get("risk_score"),
                item.get("sentiment_score"),
                item.get("url"),
            )
            for item in advisories
        ]

        with get_db() as conn:
            with conn.cursor() as cur:
                execute_batch(cur, insert_query, rows)

        logger.info(f"Upserted {len(rows)} advisories")
        return len(rows)

    # ---------------------------------------------
    # FULL RUN
    # ---------------------------------------------

    def run(self):
        logger.info("=== Travel Advisory Pipeline Started ===")

        scraped = self.scrape_all()

        if not scraped:
            logger.warning("No advisories scraped. Exiting.")
            return

        cleaned = self.clean(scraped)

        inserted = self.store(cleaned)

        logger.info(f"Pipeline completed. Records processed: {inserted}")
        logger.info("=== Pipeline Finished ===")
