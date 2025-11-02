"""
SQLite-based cache for LLM extraction results.
Used exclusively for LOCAL development to speed up seeding.

IMPORTANT: Caches RAW LLM responses (before database validation).
This allows validation logic to be re-applied when database changes.
"""
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional

from backend.settings import settings


class ExtractionCache:
    """
    Cache for RAW LLM extraction results using SQLite.

    Stores the direct LLM output (Pydantic model) BEFORE database validation.
    When retrieving from cache, validation logic is re-applied.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the extraction cache.

        Args:
            db_path: Path to SQLite database file. If None, uses settings.
        """
        if db_path is None:
            db_path = settings.llm_cache_db_path

        self.db_path = Path(db_path)
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Create the cache database and table if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extraction_cache (
                    cache_key TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    description TEXT,
                    website_text TEXT,
                    location TEXT,
                    industries TEXT,
                    target_markets TEXT,
                    business_models TEXT,
                    revenue_models TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_company_name
                ON extraction_cache(company_name)
            """)

            conn.commit()
        finally:
            conn.close()

    def _generate_cache_key(
        self,
        company_name: str,
        description: str,
        website_text: Optional[str]
    ) -> str:
        """
        Generate a cache key based on company information.

        Args:l
            company_name: Name of the company
            description: Company description
            website_text: Optional website text

        Returns:
            SHA256 hash of the combined inputs
        """
        # Combine inputs and hash them
        combined = f"{company_name}|{description}|{website_text or ''}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    def get(
        self,
        company_name: str,
        description: str,
        website_text: Optional[str]
    ) -> Optional[Dict[str, any]]:
        """
        Retrieve cached RAW LLM extraction result if it exists.

        Caller must re-apply validation logic.

        Args:
            company_name: Name of the company
            description: Company description
            website_text: Optional website text

        Returns:
            Raw LLM extraction result or None if not found
        """
        cache_key = self._generate_cache_key(company_name, description, website_text)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT location, industries, target_markets, business_models, revenue_models
                FROM extraction_cache
                WHERE cache_key = ?
            """, (cache_key,))

            row = cursor.fetchone()
            if row:
                location, industries_json, target_markets_json, business_models_json, revenue_models_json = row
                return {
                    "location": location,
                    "industries": json.loads(industries_json) if industries_json else [],
                    "target_markets": json.loads(target_markets_json) if target_markets_json else [],
                    "business_models": json.loads(business_models_json) if business_models_json else [],
                    "revenue_models": json.loads(revenue_models_json) if revenue_models_json else [],
                }
            return None
        finally:
            conn.close()

    def set(
        self,
        company_name: str,
        description: str,
        website_text: Optional[str],
        raw_llm_result: Dict[str, any]
    ):
        """
        Store RAW LLM extraction result in cache

        Args:
            company_name: Name of the company
            description: Company description
            website_text: Optional website text
            raw_llm_result: The RAW LLM extraction result to cache (Pydantic model as dict)
        """
        cache_key = self._generate_cache_key(company_name, description, website_text)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO extraction_cache
                (cache_key, company_name, description, website_text, location, industries, target_markets, business_models, revenue_models)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cache_key,
                company_name,
                description,
                website_text,
                raw_llm_result.get("location"),
                json.dumps(raw_llm_result.get("industries", [])),
                json.dumps(raw_llm_result.get("target_markets", [])),
                json.dumps(raw_llm_result.get("business_models", [])),
                json.dumps(raw_llm_result.get("revenue_models", [])),
            ))
            conn.commit()
        finally:
            conn.close()

    def clear(self):
        """Clear all cached extractions."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM extraction_cache")
            conn.commit()
        finally:
            conn.close()

extraction_cache = ExtractionCache()
