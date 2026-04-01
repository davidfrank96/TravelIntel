# TravelIntel — AI Travel Intelligence Briefings

TravelIntel is a travel intelligence briefing platform that replaces manual pre-travel research with a single, personalized, CIA-style intelligence report generated in seconds using LLMs.

## What It Does

A traveler submits six fields:

- Name
- Nationality
- Destination country
- Destination city
- Travel date
- Trip type

The system then:

1. Calls OpenAI in two passes:
   - Pass 1 extracts structured intelligence facts (risk grade, emergency numbers, consulate, hospitals, legal restrictions, cultural rules, operational guidance, key locations).
   - Pass 2 synthesizes those facts into a personalized narrative briefing.
2. Checks a PostgreSQL cache before every LLM call. If another user requested the same destination within seven days, the cached briefing is returned instantly.
3. Returns a free preview (risk grade, security snapshot, emergency numbers).
4. Unlocks the full briefing after payment and provides a downloadable PDF report.

## Quick Start (Briefing API)

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure environment

Create `.env` (see `.env.example`) and set at least:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=travel_advisories
DB_USER=postgres
DB_PASSWORD=your_password
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.4-mini
BRIEFING_CACHE_DAYS=7
```

### 3) Run the API

```bash
python -m briefing.run_api
```

API will be available at `http://localhost:8000`.

### 4) Call the API

**Preview**

```bash
POST /briefings/preview
```

**Full briefing (requires payment flag)**

```bash
POST /briefings/full
```

Include JSON:

```json
{
  "name": "Ada",
  "nationality": "Nigerian",
  "destination_country": "France",
  "destination_city": "Paris",
  "travel_date": "2026-05-10",
  "trip_type": "Business",
  "paid": true,
  "payment_reference": "stripe_123"
}
```

**PDF download**

```bash
GET /briefings/{briefing_id}/pdf
```

## Legacy Scraper Pipeline

This repo still includes the original advisory scraping pipeline (multi-source scraper + data cleaning + dashboard). It remains intact and can run in parallel, but the primary product objective is now the AI-generated traveler briefing flow described above.

Legacy entry points:
- `main.py` (scrape -> clean -> store)
- `dashboard.py` (Streamlit dashboard)

## License

See `LICENSE`.
