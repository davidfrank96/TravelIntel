"""
SQLite Database Handler (fallback compatible with PostgreSQL handler API).
"""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional


class DatabaseHandler:
    """SQLite database handler with the same core API as PostgreSQL handler."""

    def __init__(self, db_path: str = "travel_advisories.db"):
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            print(f"Database connection established: {self.db_path}")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise

    @contextmanager
    def get_cursor(self):
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            cursor.close()

    def _column_names(self, table: str) -> set:
        with self.get_cursor() as cursor:
            cursor.execute(f"PRAGMA table_info({table})")
            return {row["name"] for row in cursor.fetchall()}

    def create_tables(self):
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS travel_advisories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    country TEXT NOT NULL,
                    risk_level TEXT,
                    date TIMESTAMP,
                    description TEXT,
                    url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    country_normalized TEXT,
                    risk_level_normalized TEXT,
                    risk_score INTEGER,
                    description_cleaned TEXT,
                    keywords TEXT,
                    sentiment_score FLOAT,
                    has_security_concerns INTEGER DEFAULT 0,
                    has_safety_concerns INTEGER DEFAULT 0,
                    has_serenity_concerns INTEGER DEFAULT 0,
                    corpus_risk_grade TEXT,
                    advisory_hash TEXT
                )
                """
            )

            migration_columns = {
                "updated_at": "ALTER TABLE travel_advisories ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "country_normalized": "ALTER TABLE travel_advisories ADD COLUMN country_normalized TEXT",
                "risk_level_normalized": "ALTER TABLE travel_advisories ADD COLUMN risk_level_normalized TEXT",
                "risk_score": "ALTER TABLE travel_advisories ADD COLUMN risk_score INTEGER",
                "description_cleaned": "ALTER TABLE travel_advisories ADD COLUMN description_cleaned TEXT",
                "keywords": "ALTER TABLE travel_advisories ADD COLUMN keywords TEXT",
                "sentiment_score": "ALTER TABLE travel_advisories ADD COLUMN sentiment_score FLOAT",
                "has_security_concerns": "ALTER TABLE travel_advisories ADD COLUMN has_security_concerns INTEGER DEFAULT 0",
                "has_safety_concerns": "ALTER TABLE travel_advisories ADD COLUMN has_safety_concerns INTEGER DEFAULT 0",
                "has_serenity_concerns": "ALTER TABLE travel_advisories ADD COLUMN has_serenity_concerns INTEGER DEFAULT 0",
                "corpus_risk_grade": "ALTER TABLE travel_advisories ADD COLUMN corpus_risk_grade TEXT",
                "advisory_hash": "ALTER TABLE travel_advisories ADD COLUMN advisory_hash TEXT",
            }
            existing = self._column_names("travel_advisories")
            for col, ddl in migration_columns.items():
                if col not in existing:
                    cursor.execute(ddl)

            cursor.execute(
                "CREATE TABLE IF NOT EXISTS processed_advisories ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "advisory_id INTEGER,"
                "country_normalized TEXT,"
                "risk_level_normalized TEXT,"
                "risk_score INTEGER,"
                "keywords TEXT,"
                "sentiment_score FLOAT,"
                "has_security_concerns INTEGER DEFAULT 0,"
                "has_safety_concerns INTEGER DEFAULT 0,"
                "has_serenity_concerns INTEGER DEFAULT 0,"
                "processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )

            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_advisories_hash ON travel_advisories(advisory_hash)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_advisories_country_norm ON travel_advisories(country_normalized)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_advisories_source ON travel_advisories(source)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_advisories_date ON travel_advisories(date)"
            )

    def _coerce_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    def _build_advisory_hash(self, advisory: Dict, date_val: Optional[datetime]) -> str:
        source = str(advisory.get("source") or "").strip().lower()
        country = str(advisory.get("country_normalized") or advisory.get("country") or "").strip().lower()
        url = str(advisory.get("url") or "").strip().lower()
        risk = str(advisory.get("risk_level_normalized") or advisory.get("risk_level") or "").strip().lower()
        desc = str(advisory.get("description_cleaned") or advisory.get("description") or "").strip().lower()[:200]
        if date_val:
            key = f"{source}|{country}|{url}|{date_val.date().isoformat()}"
        else:
            key = f"{source}|{country}|{url}|{risk}|{desc}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def insert_advisories(self, advisories: List[Dict]) -> int:
        if not advisories:
            return 0

        count = 0
        with self.get_cursor() as cursor:
            for adv in advisories:
                date_val = self._coerce_datetime(adv.get("date_parsed") or adv.get("date") or adv.get("scraped_at"))
                scraped_at_val = self._coerce_datetime(adv.get("scraped_at")) or datetime.utcnow()
                advisory_hash = self._build_advisory_hash(adv, date_val)
                keywords_json = json.dumps(adv.get("keywords") if isinstance(adv.get("keywords"), list) else [])

                cursor.execute(
                    """
                    INSERT INTO travel_advisories (
                        source, country, risk_level, date, description, url, scraped_at,
                        country_normalized, risk_level_normalized, risk_score, description_cleaned,
                        keywords, sentiment_score, has_security_concerns, has_safety_concerns,
                        has_serenity_concerns, corpus_risk_grade, advisory_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(advisory_hash) DO UPDATE SET
                        risk_level = excluded.risk_level,
                        date = excluded.date,
                        description = excluded.description,
                        url = excluded.url,
                        scraped_at = excluded.scraped_at,
                        updated_at = CURRENT_TIMESTAMP,
                        country_normalized = excluded.country_normalized,
                        risk_level_normalized = excluded.risk_level_normalized,
                        risk_score = excluded.risk_score,
                        description_cleaned = excluded.description_cleaned,
                        keywords = excluded.keywords,
                        sentiment_score = excluded.sentiment_score,
                        has_security_concerns = excluded.has_security_concerns,
                        has_safety_concerns = excluded.has_safety_concerns,
                        has_serenity_concerns = excluded.has_serenity_concerns,
                        corpus_risk_grade = excluded.corpus_risk_grade
                    """,
                    (
                        adv.get("source", ""),
                        adv.get("country", ""),
                        adv.get("risk_level", ""),
                        date_val,
                        adv.get("description", ""),
                        adv.get("url", ""),
                        scraped_at_val,
                        adv.get("country_normalized"),
                        adv.get("risk_level_normalized"),
                        adv.get("risk_score"),
                        adv.get("description_cleaned"),
                        keywords_json,
                        adv.get("sentiment_score", 0.0),
                        1 if adv.get("has_security_concerns") else 0,
                        1 if adv.get("has_safety_concerns") else 0,
                        1 if adv.get("has_serenity_concerns") else 0,
                        adv.get("corpus_risk_grade"),
                        advisory_hash,
                    ),
                )
                count += 1
        return count

    def insert_processed_data(self, processed_data: List[Dict]) -> int:
        count = 0
        with self.get_cursor() as cursor:
            for data in processed_data:
                keywords_json = json.dumps(data.get("keywords", []))
                cursor.execute(
                    """
                    INSERT INTO processed_advisories (
                        advisory_id, country_normalized, risk_level_normalized, risk_score,
                        keywords, sentiment_score, has_security_concerns, has_safety_concerns,
                        has_serenity_concerns
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data.get("advisory_id"),
                        data.get("country_normalized", ""),
                        data.get("risk_level_normalized", ""),
                        data.get("risk_score", 0),
                        keywords_json,
                        data.get("sentiment_score", 0.0),
                        1 if data.get("has_security_concerns") else 0,
                        1 if data.get("has_safety_concerns") else 0,
                        1 if data.get("has_serenity_concerns") else 0,
                    ),
                )
                count += 1
        return count

    def get_advisories(
        self, country: Optional[str] = None, source: Optional[str] = None, limit: int = 5000
    ) -> List[Dict]:
        query = "SELECT * FROM travel_advisories WHERE 1=1"
        params = []
        if country:
            query += " AND country_normalized LIKE ?"
            params.append(f"%{country}%")
        if source:
            query += " AND source = ?"
            params.append(source)
        query += " ORDER BY COALESCE(date, scraped_at) DESC LIMIT ?"
        params.append(limit)

        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            raw_keywords = d.get("keywords")
            if isinstance(raw_keywords, str):
                try:
                    d["keywords"] = json.loads(raw_keywords)
                except Exception:
                    d["keywords"] = []
            elif raw_keywords is None:
                d["keywords"] = []
            result.append(d)
        return result

    def get_all_countries(self) -> List[str]:
        with self.get_cursor() as cursor:
            cursor.execute("SELECT DISTINCT country_normalized FROM travel_advisories ORDER BY country_normalized")
            rows = cursor.fetchall()
        return [row["country_normalized"] for row in rows if row["country_normalized"]]

    def close(self):
        if self.conn:
            self.conn.close()
            print("Database connection closed")

    def __del__(self):
        self.close()
