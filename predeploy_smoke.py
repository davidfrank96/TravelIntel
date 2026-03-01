"""
Pre-deploy smoke test:
1) scrape a small advisory sample
2) clean + store in Postgres
3) verify dashboard data load path
"""

import os
import sys

from dotenv import load_dotenv


def fail(msg: str, code: int = 1):
    print(f"[FAIL] {msg}")
    sys.exit(code)


def require_env(name: str):
    value = os.getenv(name)
    if value is None or str(value).strip() == "":
        fail(f"Missing required env var: {name}")


def main():
    load_dotenv()
    for var in ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]:
        require_env(var)

    os.environ["DB_BACKEND"] = "postgres"
    os.environ.setdefault("FCDO_MAX_ROWS", "8")

    # Import after env preflight so config.py can initialize safely.
    from data_cleaner import DataCleaner
    from db_factory import get_handler
    from dashboard import load_data
    from scrapers import UKFCDOScraper
    import config

    print("[1/4] Scraping UK FCDO sample...")
    scraper = UKFCDOScraper(
        url=config.TARGET_URLS["uk_fcdo"],
    )
    raw = scraper.scrape()
    if hasattr(scraper, "close"):
        scraper.close()
    if not raw:
        fail("No advisories scraped from UK FCDO sample.")
    print(f"[OK] scraped={len(raw)}")

    print("[2/4] Cleaning and quality filtering...")
    cleaner = DataCleaner()
    cleaned = cleaner.deduplicate(cleaner.clean_batch(raw))
    quality = []
    for adv in cleaned:
        country_ok = (adv.get("country_normalized") or adv.get("country") or "").strip().lower() != "unknown"
        risk_ok = (adv.get("risk_score") or 0) > 0
        desc = (adv.get("description_cleaned") or adv.get("description") or "").strip()
        text_ok = len(desc) >= 40
        if country_ok and (risk_ok or text_ok):
            quality.append(adv)
    if not quality:
        fail("No quality advisories after cleaning.")
    print(f"[OK] quality={len(quality)}")

    print("[3/4] Writing to Postgres...")
    db = get_handler()
    inserted = db.insert_advisories(quality)
    db.close()
    if inserted <= 0:
        fail("Insert returned 0 rows.")
    print(f"[OK] inserted={inserted}")

    print("[4/4] Checking dashboard data path...")
    df = load_data(source_filter="UK FCDO", days_back=3650)
    required_cols = ["country_normalized", "risk_score", "risk_reason", "risk_keywords"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        fail(f"Dashboard load missing columns: {missing}")
    if len(df) == 0:
        fail("Dashboard load returned 0 rows.")
    print(f"[OK] dashboard_rows={len(df)}")

    print("\nSmoke test passed.")


if __name__ == "__main__":
    main()
