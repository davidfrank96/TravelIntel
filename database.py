"""
PostgreSQL Database Handler
"""
import psycopg2, psycopg2.extras
from psycopg2.extras import execute_values
from psycopg2 import sql
from typing import List, Dict, Optional
from datetime import datetime
import hashlib
import config
from contextlib import contextmanager


class DatabaseHandler:
    """Handles all database operations for travel advisories"""
    
    def __init__(self):
        """Initialize database connection"""
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=config.DATABASE_CONFIG['host'],
                port=config.DATABASE_CONFIG['port'],
                database=config.DATABASE_CONFIG['database'],
                user=config.DATABASE_CONFIG['user'],
                password=config.DATABASE_CONFIG['password']
            )
            self.conn.autocommit = False
            print("Database connection established")

        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
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
    
    def create_tables(self):
        """Create necessary database tables"""
        with self.get_cursor() as cursor:
            # Main advisories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS travel_advisories (
                    id SERIAL PRIMARY KEY,                          -- Core fields
                    source VARCHAR(100) NOT NULL,                 --
                    country VARCHAR(200) NOT NULL,                --
                    risk_level VARCHAR(255),                      -- Raw risk level text
                    date TIMESTAMP,                               --
                    description TEXT,                             -- Raw description
                    url TEXT,                                     --
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, --
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, --
                    country_normalized VARCHAR(200),              -- Processed fields
                    risk_level_normalized VARCHAR(50),            --
                    risk_score INTEGER,                           --
                    description_cleaned TEXT,                     --
                    keywords TEXT[],                              --
                    sentiment_score FLOAT,                        --
                    has_security_concerns BOOLEAN DEFAULT FALSE,  --
                    has_safety_concerns BOOLEAN DEFAULT FALSE,    --
                    has_serenity_concerns BOOLEAN DEFAULT FALSE,  --
                    corpus_risk_grade VARCHAR(5),                 -- New A-E Grade
                    advisory_hash VARCHAR(64),                    -- Stable upsert key for null-date rows
                    UNIQUE(source, country, date)                 -- Uniqueness constraint
                )
            """)
            
            # Schema Migration: Ensure columns exist if table was created with older schema
            migration_queries = [
                "ALTER TABLE travel_advisories ADD COLUMN IF NOT EXISTS country_normalized VARCHAR(200)",
                "ALTER TABLE travel_advisories ADD COLUMN IF NOT EXISTS risk_level_normalized VARCHAR(50)",
                "ALTER TABLE travel_advisories ADD COLUMN IF NOT EXISTS risk_score INTEGER",
                "ALTER TABLE travel_advisories ADD COLUMN IF NOT EXISTS description_cleaned TEXT",
                "ALTER TABLE travel_advisories ADD COLUMN IF NOT EXISTS keywords TEXT[]",
                "ALTER TABLE travel_advisories ADD COLUMN IF NOT EXISTS sentiment_score FLOAT",
                "ALTER TABLE travel_advisories ADD COLUMN IF NOT EXISTS has_security_concerns BOOLEAN DEFAULT FALSE",
                "ALTER TABLE travel_advisories ADD COLUMN IF NOT EXISTS has_safety_concerns BOOLEAN DEFAULT FALSE",
                "ALTER TABLE travel_advisories ADD COLUMN IF NOT EXISTS has_serenity_concerns BOOLEAN DEFAULT FALSE",
                "ALTER TABLE travel_advisories ADD COLUMN IF NOT EXISTS corpus_risk_grade VARCHAR(5)",
                "ALTER TABLE travel_advisories ADD COLUMN IF NOT EXISTS advisory_hash VARCHAR(64)"
            ]
            for query in migration_queries:
                cursor.execute(query)

            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_advisories_hash
                ON travel_advisories(advisory_hash)
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_advisories_country 
                ON travel_advisories(country_normalized)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_advisories_source 
                ON travel_advisories(source)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_advisories_date 
                ON travel_advisories(date)
            """)
            
            print("Database tables created/verified")

    def _coerce_datetime(self, value):
        """Coerce a value to datetime where possible."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None

    def _build_advisory_hash(self, advisory: Dict, date_val: Optional[datetime]) -> str:
        """
        Build a stable upsert key.
        If date is available, include it; otherwise use content/url fallback.
        """
        source = str(advisory.get('source') or '').strip().lower()
        country = str(advisory.get('country_normalized') or advisory.get('country') or '').strip().lower()
        url = str(advisory.get('url') or '').strip().lower()
        risk = str(advisory.get('risk_level_normalized') or advisory.get('risk_level') or '').strip().lower()
        desc = str(advisory.get('description_cleaned') or advisory.get('description') or '').strip().lower()[:200]

        if date_val:
            key = f"{source}|{country}|{url}|{date_val.date().isoformat()}"
        else:
            key = f"{source}|{country}|{url}|{risk}|{desc}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()
    
    def insert_advisories(self, advisories: List[Dict]) -> int: 
        """Insert or update travel advisories in a batch."""
        if not advisories:
            return 0

        # Define all columns to be inserted/updated
        columns = [
            'source', 'country', 'risk_level', 'date', 'description', 'url', 'scraped_at',
            'country_normalized', 'risk_level_normalized', 'risk_score', 'description_cleaned',
            'keywords', 'sentiment_score', 'has_security_concerns', 'has_safety_concerns', 
            'has_serenity_concerns', 'corpus_risk_grade', 'advisory_hash'
        ]

        # Prepare data tuples
        data_to_insert = []
        for adv in advisories:
            date_val = self._coerce_datetime(adv.get('date_parsed') or adv.get('date') or adv.get('scraped_at'))
            scraped_at_val = self._coerce_datetime(adv.get('scraped_at')) or datetime.utcnow()
            advisory_hash = self._build_advisory_hash(adv, date_val)

            row = {
                'source': adv.get('source'),
                'country': adv.get('country'),
                'risk_level': adv.get('risk_level'),
                'date': date_val,
                'description': adv.get('description'),
                'url': adv.get('url'),
                'scraped_at': scraped_at_val,
                'country_normalized': adv.get('country_normalized'),
                'risk_level_normalized': adv.get('risk_level_normalized'),
                'risk_score': adv.get('risk_score'),
                'description_cleaned': adv.get('description_cleaned'),
                'keywords': adv.get('keywords') if isinstance(adv.get('keywords'), list) else [],
                'sentiment_score': adv.get('sentiment_score'),
                'has_security_concerns': bool(adv.get('has_security_concerns', False)),
                'has_safety_concerns': bool(adv.get('has_safety_concerns', False)),
                'has_serenity_concerns': bool(adv.get('has_serenity_concerns', False)),
                'corpus_risk_grade': adv.get('corpus_risk_grade'),
                'advisory_hash': advisory_hash,
            }
            data_to_insert.append(tuple(row.get(col) for col in columns))

        with self.get_cursor() as cursor:
            # Using psycopg2.extras.execute_values for efficient batch insert
            insert_query = sql.SQL("""
                INSERT INTO travel_advisories ({fields}) VALUES %s
                ON CONFLICT (advisory_hash) DO UPDATE SET
                    risk_level = EXCLUDED.risk_level,
                    date = EXCLUDED.date,
                    description = EXCLUDED.description,
                    url = EXCLUDED.url,
                    scraped_at = EXCLUDED.scraped_at,
                    updated_at = CURRENT_TIMESTAMP,
                    country_normalized = EXCLUDED.country_normalized,
                    risk_level_normalized = EXCLUDED.risk_level_normalized,
                    risk_score = EXCLUDED.risk_score,
                    description_cleaned = EXCLUDED.description_cleaned,
                    keywords = EXCLUDED.keywords,
                    sentiment_score = EXCLUDED.sentiment_score,
                    has_security_concerns = EXCLUDED.has_security_concerns,
                    has_safety_concerns = EXCLUDED.has_safety_concerns,
                    has_serenity_concerns = EXCLUDED.has_serenity_concerns,
                    corpus_risk_grade = EXCLUDED.corpus_risk_grade
            """).format(fields=sql.SQL(', ').join(map(sql.Identifier, columns)))
            
            psycopg2.extras.execute_values(cursor, insert_query, data_to_insert)
            return cursor.rowcount
    
    def get_advisories(self, country: Optional[str] = None, 
                      source: Optional[str] = None,
                      limit: int = 100) -> List[Dict]:
        """Retrieve advisories from database"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM travel_advisories WHERE 1=1"
            params = []
            
            if country:
                query += " AND country_normalized ILIKE %s"
                params.append(f"%{country}%")
            
            if source:
                query += " AND source = %s"
                params.append(source)
            
            query += " ORDER BY scraped_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return results
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")
