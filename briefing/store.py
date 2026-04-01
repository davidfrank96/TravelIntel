"""PostgreSQL cache storage for generated briefings."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

import config


class BriefingStore:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=config.DATABASE_CONFIG["host"],
            port=config.DATABASE_CONFIG["port"],
            database=config.DATABASE_CONFIG["database"],
            user=config.DATABASE_CONFIG["user"],
            password=config.DATABASE_CONFIG["password"],
        )
        self.conn.autocommit = True
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS briefing_cache (
                    briefing_id UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    nationality TEXT NOT NULL,
                    destination_country TEXT NOT NULL,
                    destination_city TEXT NOT NULL,
                    travel_date DATE,
                    trip_type TEXT NOT NULL,
                    facts_json JSONB,
                    narrative TEXT,
                    risk_grade TEXT,
                    security_snapshot TEXT,
                    emergency_numbers JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP,
                    payment_reference TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_briefing_cache_key
                ON briefing_cache (nationality, destination_country, destination_city, trip_type, created_at)
                """
            )

    def get_cached(
        self,
        nationality: str,
        destination_country: str,
        destination_city: str,
        trip_type: str,
        max_age_days: int,
    ) -> Optional[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM briefing_cache
                WHERE nationality = %s
                  AND destination_country = %s
                  AND destination_city = %s
                  AND trip_type = %s
                  AND created_at >= %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (nationality, destination_country, destination_city, trip_type, cutoff),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def save_briefing(
        self,
        payload: Dict[str, Any],
        facts: Dict[str, Any],
        narrative: str,
        risk_grade: str,
        security_snapshot: str,
        emergency_numbers: Any,
    ) -> Dict[str, Any]:
        briefing_id = uuid.uuid4()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO briefing_cache (
                    briefing_id, name, nationality, destination_country, destination_city,
                    travel_date, trip_type, facts_json, narrative, risk_grade,
                    security_snapshot, emergency_numbers
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    str(briefing_id),
                    payload.get("name"),
                    payload.get("nationality"),
                    payload.get("destination_country"),
                    payload.get("destination_city"),
                    payload.get("travel_date"),
                    payload.get("trip_type"),
                    json.dumps(facts),
                    narrative,
                    risk_grade,
                    security_snapshot,
                    json.dumps(emergency_numbers),
                ),
            )
            row = cur.fetchone()
            return dict(row)

    def mark_paid(self, briefing_id: str, payment_reference: Optional[str] = None) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE briefing_cache
                   SET paid_at = CURRENT_TIMESTAMP,
                       payment_reference = %s,
                       updated_at = CURRENT_TIMESTAMP
                 WHERE briefing_id = %s
                """,
                (payment_reference, briefing_id),
            )

    def get_briefing(self, briefing_id: str) -> Optional[Dict[str, Any]]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM briefing_cache WHERE briefing_id = %s",
                (briefing_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
