"""
Main Orchestration Script for Travel Advisory Scraper
HTTP-only, manual scraping (no Playwright/Selenium)
"""

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from database_sqlite import DatabaseHandler
from data_cleaner import DataCleaner
from ai_predictor import InsightAnalyzer
from nlp_vectorizer import LemmatizingTfidfVectorizer


def scrape_all() -> List[Dict]:
    """Scrape all configured sources via HTTP requests only"""
    all_advisories = []


@st.cache_data(show_spinner=False)
def load_data(country_filter=None, source_filter=None, days_back: int = 365):
    db = DatabaseHandler()
    try:
        advisories = db.get_advisories(
            country=country_filter,
            source=source_filter,
            limit=5000,
        )
    finally:
        db.close()

            if advisories:
                print(f"  ✓ Found {len(advisories)} advisories from {source_name}")
                all_advisories.extend(advisories)
            else:
                print(f"  ✗ No advisories found from {source_name}")

            # Rate limiting
            time.sleep(2)

        except Exception as e:
            print(f"  ✗ Error scraping {source_name}: {e}")
            continue

    print(f"\nTotal advisories scraped: {len(all_advisories)}")
    return all_advisories


def clean_data(advisories: List[Dict]) -> List[Dict]:
    """Clean and normalize scraped data"""
    print("\n" + "=" * 60)
    print("Cleaning Data")
    print("=" * 60)

    cleaner = DataCleaner()
    cleaned = cleaner.clean_batch(advisories)
    deduplicated = cleaner.deduplicate(cleaned)

    print(f"Cleaned {len(cleaned)} advisories")
    print(f"After deduplication: {len(deduplicated)} advisories")

    return deduplicated


def store_data(advisories: List[Dict]):
    """Store cleaned data in database"""
    print("\n" + "=" * 60)
    print("Storing Data in Database")
    print("=" * 60)

    db = DatabaseHandler()
    inserted = db.insert_advisories(advisories)
    print(f"Inserted/Updated {inserted} advisories in database")

    # Optional: store processed data for analytics
    processed_data = []
    for advisory in advisories:
        processed_data.append({
            'advisory_id': None,
            'country_normalized': advisory.get('country_normalized'),
            'risk_level_normalized': advisory.get('risk_level_normalized'),
            'risk_score': advisory.get('risk_score'),
            'keywords': advisory.get('keywords', []),
            'sentiment_score': advisory.get('sentiment_score', 0.0),
            'has_security_concerns': advisory.get('has_security_concerns', False),
            'has_safety_concerns': advisory.get('has_safety_concerns', False),
            'has_serenity_concerns': advisory.get('has_serenity_concerns', False)
        })

    if processed_data:
        db.insert_processed_data(processed_data)
        print(f"Stored {len(processed_data)} processed records")

    db.close()


def run_pipeline():
    """Run the full pipeline manually"""
    print("\n" + "=" * 60)
    print("TRAVEL ADVISORY SCRAPER PIPELINE")
    print("=" * 60)

    st.sidebar.header("Filters")

    country_input = st.sidebar.text_input(
        "Country (optional, partial name allowed)", value=""
    )
    source_input = st.sidebar.selectbox(
        "Source",
        options=[
            "All",
            "US State Department",
            "UK FCDO",
            "Smart Traveller (Australia)",
            "IATA Travel Centre",
            "Canada Travel",
        ],
    )
    days_back = st.sidebar.slider(
        "Look back (days)", min_value=30, max_value=730, value=365, step=30
    )

    source_filter = None if source_input == "All" else source_input
    country_filter = country_input if country_input.strip() else None

        # Step 2: Clean
        cleaned_advisories = clean_data(advisories)

        # Step 3: Store
        store_data(cleaned_advisories)

        print("\nPipeline completed successfully!")

    except Exception as e:
        print(f"\nError in pipeline: {e}")
        raise
