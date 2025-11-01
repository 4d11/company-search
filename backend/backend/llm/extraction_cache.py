"""
SQLite-based cache for LLM extraction results.
Used exclusively for LOCAL development to speed up seeding.
"""
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional

from backend.settings import settings


class ExtractionCache:
    """Cache for LLM extraction results using SQLite."""

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
        Retrieve cached extraction result if it exists.

        Args:
            company_name: Name of the company
            description: Company description
            website_text: Optional website text

        Returns:
            Cached extraction result or None if not found
        """
        cache_key = self._generate_cache_key(company_name, description, website_text)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT location, industries, target_markets
                FROM extraction_cache
                WHERE cache_key = ?
            """, (cache_key,))

            row = cursor.fetchone()
            if row:
                location, industries_json, target_markets_json = row
                return {
                    "location": location,
                    "industries": json.loads(industries_json),
                    "target_markets": json.loads(target_markets_json)
                }
            return None
        finally:
            conn.close()

    def set(
        self,
        company_name: str,
        description: str,
        website_text: Optional[str],
        extraction_result: Dict[str, any]
    ):
        """
        Store extraction result in cache.

        Args:
            company_name: Name of the company
            description: Company description
            website_text: Optional website text
            extraction_result: The extraction result to cache
        """
        cache_key = self._generate_cache_key(company_name, description, website_text)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO extraction_cache
                (cache_key, company_name, description, website_text, location, industries, target_markets)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                cache_key,
                company_name,
                description,
                website_text,
                extraction_result["location"],
                json.dumps(extraction_result["industries"]),
                json.dumps(extraction_result["target_markets"])
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

    def stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM extraction_cache")
            count = cursor.fetchone()[0]
            return {"cached_entries": count}
        finally:
            conn.close()


# Global cache instance
extraction_cache = ExtractionCache()
