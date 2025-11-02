"""
Tests for LLM extraction cache.
"""
import pytest

from backend.llm.extraction_cache import ExtractionCache


class TestExtractionCache:
    """Test suite for ExtractionCache."""

    def test_cache_initialization(self, temp_cache_db):
        """Test that cache initializes correctly."""
        cache = ExtractionCache(db_path=temp_cache_db)
        assert cache.db_path.exists()

    def test_cache_key_generation(self, temp_cache_db):
        """Test that cache keys are generated consistently."""
        cache = ExtractionCache(db_path=temp_cache_db)

        key1 = cache._generate_cache_key("Company A", "Description 1", "Website text")
        key2 = cache._generate_cache_key("Company A", "Description 1", "Website text")
        key3 = cache._generate_cache_key("Company B", "Description 1", "Website text")

        # Same inputs should produce same key
        assert key1 == key2
        # Different inputs should produce different key
        assert key1 != key3

    def test_cache_miss(self, temp_cache_db):
        """Test that cache returns None when key doesn't exist."""
        cache = ExtractionCache(db_path=temp_cache_db)

        result = cache.get("Company A", "Description", "Website")
        assert result is None

    def test_cache_set_and_get(self, temp_cache_db):
        """Test that cached values can be stored and retrieved."""
        cache = ExtractionCache(db_path=temp_cache_db)

        extraction_result = {
            "location": "San Francisco",
            "industries": ["SaaS", "AI/ML"],
            "target_markets": ["SMB", "Enterprise"]
        }

        # Store in cache
        cache.set("Company A", "Description", "Website", extraction_result)

        # Retrieve from cache
        cached = cache.get("Company A", "Description", "Website")

        assert cached is not None
        assert cached["location"] == "San Francisco"
        assert cached["industries"] == ["SaaS", "AI/ML"]
        assert cached["target_markets"] == ["SMB", "Enterprise"]

    def test_cache_update(self, temp_cache_db):
        """Test that cache can be updated with new values."""
        cache = ExtractionCache(db_path=temp_cache_db)

        original = {
            "location": "San Francisco",
            "industries": ["SaaS"],
            "target_markets": ["SMB"]
        }

        updated = {
            "location": "New York",
            "industries": ["FinTech"],
            "target_markets": ["Enterprise"]
        }

        # Store original
        cache.set("Company A", "Description", "Website", original)

        # Update with new values
        cache.set("Company A", "Description", "Website", updated)

        # Retrieve should get updated values
        cached = cache.get("Company A", "Description", "Website")

        assert cached["location"] == "New York"
        assert cached["industries"] == ["FinTech"]
        assert cached["target_markets"] == ["Enterprise"]

    def test_cache_null_location(self, temp_cache_db):
        """Test that null location is handled correctly."""
        cache = ExtractionCache(db_path=temp_cache_db)

        extraction_result = {
            "location": None,
            "industries": ["SaaS"],
            "target_markets": ["SMB"]
        }

        cache.set("Company A", "Description", "Website", extraction_result)
        cached = cache.get("Company A", "Description", "Website")

        assert cached["location"] is None

    def test_cache_empty_lists(self, temp_cache_db):
        """Test that empty lists are handled correctly."""
        cache = ExtractionCache(db_path=temp_cache_db)

        extraction_result = {
            "location": None,
            "industries": [],
            "target_markets": []
        }

        cache.set("Company A", "Description", "Website", extraction_result)
        cached = cache.get("Company A", "Description", "Website")

        assert cached["industries"] == []
        assert cached["target_markets"] == []

    def test_cache_stats(self, temp_cache_db):
        """Test cache statistics."""
        cache = ExtractionCache(db_path=temp_cache_db)

        # Initially empty
        stats = cache.stats()
        assert stats["cached_entries"] == 0

        # Add entries
        for i in range(5):
            cache.set(f"Company {i}", "Description", "Website", {
                "location": "San Francisco",
                "industries": ["SaaS"],
                "target_markets": ["SMB"]
            })

        stats = cache.stats()
        assert stats["cached_entries"] == 5

    def test_cache_clear(self, temp_cache_db):
        """Test cache clearing."""
        cache = ExtractionCache(db_path=temp_cache_db)

        # Add entries
        for i in range(3):
            cache.set(f"Company {i}", "Description", "Website", {
                "location": "San Francisco",
                "industries": ["SaaS"],
                "target_markets": ["SMB"]
            })

        # Verify entries exist
        stats = cache.stats()
        assert stats["cached_entries"] == 3

        # Clear cache
        cache.clear()

        # Verify cache is empty
        stats = cache.stats()
        assert stats["cached_entries"] == 0

    def test_cache_with_none_website_text(self, temp_cache_db):
        """Test caching with None website_text."""
        cache = ExtractionCache(db_path=temp_cache_db)

        extraction_result = {
            "location": "San Francisco",
            "industries": ["SaaS"],
            "target_markets": ["SMB"]
        }

        cache.set("Company A", "Description", None, extraction_result)
        cached = cache.get("Company A", "Description", None)

        assert cached is not None
        assert cached["location"] == "San Francisco"

    def test_different_descriptions_different_cache(self, temp_cache_db):
        """Test that different descriptions produce different cache entries."""
        cache = ExtractionCache(db_path=temp_cache_db)

        result1 = {
            "location": "San Francisco",
            "industries": ["SaaS"],
            "target_markets": ["SMB"]
        }

        result2 = {
            "location": "New York",
            "industries": ["FinTech"],
            "target_markets": ["Enterprise"]
        }

        cache.set("Company A", "Description 1", "Website", result1)
        cache.set("Company A", "Description 2", "Website", result2)

        # Different descriptions should retrieve different results
        cached1 = cache.get("Company A", "Description 1", "Website")
        cached2 = cache.get("Company A", "Description 2", "Website")

        assert cached1["location"] == "San Francisco"
        assert cached2["location"] == "New York"
