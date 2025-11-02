"""
In-memory cache for LLM-generated company explanations.

Caches explanations by (company_id, normalized_query) to maximize cache hits
when users slightly modify their searches.

Example:
  "AI companies in NYC" → normalized: "ai companies nyc"
  "AI startups in NYC" → normalized: "ai startups nyc"
  Both will share cached results for overlapping companies.
"""
import hashlib
import re
import time
from typing import Dict, Optional, Tuple
from collections import OrderedDict


class ExplanationCache:
    """
    LRU cache with TTL for company explanations.

    Cache key: (company_id, query_hash)
    Cache value: (explanation, timestamp)
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of cached entries (LRU eviction)
            ttl_seconds: Time-to-live for cache entries (default 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[Tuple[int, str], Tuple[str, float]] = OrderedDict()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, company_id: int, query: str) -> Optional[str]:
        """
        Get cached explanation for company and query.

        Args:
            company_id: Company ID
            query: Original query text

        Returns:
            Cached explanation if found and not expired, None otherwise
        """
        query_hash = self._normalize_query(query)
        key = (company_id, query_hash)

        if key not in self._cache:
            self._misses += 1
            return None

        explanation, timestamp = self._cache[key]

        # Check if expired
        if time.time() - timestamp > self.ttl_seconds:
            # Remove expired entry
            del self._cache[key]
            self._misses += 1
            return None

        # Move to end (mark as recently used)
        self._cache.move_to_end(key)
        self._hits += 1

        return explanation

    def set(self, company_id: int, query: str, explanation: str):
        """
        Cache an explanation.

        Args:
            company_id: Company ID
            query: Original query text
            explanation: Explanation to cache
        """
        query_hash = self._normalize_query(query)
        key = (company_id, query_hash)

        # Remove if already exists (to update timestamp and position)
        if key in self._cache:
            del self._cache[key]

        # Add new entry
        self._cache[key] = (explanation, time.time())

        # Evict oldest if over capacity
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)  # Remove oldest (first) item
            self._evictions += 1

    def get_batch(self, company_ids: list[int], query: str) -> Dict[int, str]:
        """
        Get cached explanations for multiple companies.

        Args:
            company_ids: List of company IDs
            query: Query text

        Returns:
            Dict mapping company_id -> explanation for cache hits
        """
        results = {}

        for company_id in company_ids:
            explanation = self.get(company_id, query)
            if explanation:
                results[company_id] = explanation

        return results

    def set_batch(self, explanations: Dict[int, str], query: str):
        """
        Cache multiple explanations at once.

        Args:
            explanations: Dict mapping company_id -> explanation
            query: Query text
        """
        for company_id, explanation in explanations.items():
            self.set(company_id, query, explanation)

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_seconds": self.ttl_seconds,
        }

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query to maximize cache hits for similar queries.

        Normalization steps:
        1. Lowercase
        2. Remove punctuation
        3. Remove extra whitespace
        4. Sort words (so "AI NYC" == "NYC AI")
        5. Hash the result for compact storage

        Args:
            query: Original query text

        Returns:
            Hash of normalized query
        """
        if not query:
            return ""

        # Lowercase
        normalized = query.lower()

        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        # Sort words to handle word order variations
        words = sorted(normalized.split())
        normalized = ' '.join(words)

        # Hash for compact storage (MD5 is fast and collision-resistant enough)
        query_hash = hashlib.md5(normalized.encode()).hexdigest()

        return query_hash


# Global cache instance
_explanation_cache: Optional[ExplanationCache] = None


def get_explanation_cache() -> ExplanationCache:
    """
    Get the global explanation cache singleton.

    Returns:
        ExplanationCache instance
    """
    global _explanation_cache

    if _explanation_cache is None:
        _explanation_cache = ExplanationCache(
            max_size=1000,  # Cache up to 1000 company×query pairs
            ttl_seconds=3600  # 1 hour TTL
        )

    return _explanation_cache


def clear_cache():
    """Clear the global cache (useful for testing)."""
    cache = get_explanation_cache()
    cache.clear()
