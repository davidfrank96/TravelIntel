"""
Quick script to check if database has data.
"""

from db_factory import get_handler


db = get_handler()

try:
    advisories = db.get_advisories(limit=5)
    total = len(db.get_advisories(limit=99999))
    print(f"\nTotal advisories in database: {total}")

    if advisories:
        print(f"\nFound {len(advisories)} recent advisories:")
        for adv in advisories[:3]:
            print(f"  - {adv.get('country')} ({adv.get('source')}): {adv.get('date')}")
    else:
        print("\nNo advisories found - scraper may not have run yet")

    if hasattr(db, "get_all_countries"):
        countries = db.get_all_countries()
        if countries:
            print(f"\nCountries in database: {len(countries)}")
            print(f"  Sample: {', '.join(countries[:5])}")
finally:
    db.close()
