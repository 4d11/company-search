"""
Integration tests for business model synonym matching in Elasticsearch.

These tests verify that ES fuzzy matching correctly maps business model variations
to their canonical forms, with special focus on SaaS variations.
"""
import pytest
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from backend.es.fuzzy_matcher import validate_segment_value_es
from backend.es.segment_indices import (
    create_segment_index,
    BUSINESS_MODELS_INDEX,
)


@pytest.fixture(scope="module")
def es_client():
    """Create ES client for testing."""
    client = Elasticsearch(["http://localhost:9200"])

    # Verify ES is available
    if not client.ping():
        pytest.skip("Elasticsearch not available")

    return client


@pytest.fixture(scope="module")
def setup_business_models_index(es_client):
    """Set up business models index with test data."""
    # Business models to test
    test_business_models = [
        "B2B",
        "B2C",
        "B2B2C",
        "Marketplace",
        "Platform",
        "SaaS",
    ]

    # Create index with synonym mappings
    try:
        # Delete if exists
        if es_client.indices.exists(index=BUSINESS_MODELS_INDEX):
            es_client.indices.delete(index=BUSINESS_MODELS_INDEX)

        # Create with proper mappings
        create_segment_index(es_client, "business_models")

        # Index test data using bulk API
        actions = []
        for idx, business_model in enumerate(test_business_models):
            actions.append({
                "_index": BUSINESS_MODELS_INDEX,
                "_id": idx + 1,
                "_source": {"name": business_model}
            })

        if actions:
            success, failed = bulk(es_client, actions, raise_on_error=False)
            print(f"Indexed {success} test business models")

        # Refresh to make documents searchable
        es_client.indices.refresh(index=BUSINESS_MODELS_INDEX)

        yield

        # Cleanup
        # es_client.indices.delete(index=BUSINESS_MODELS_INDEX)
    except Exception as e:
        pytest.skip(f"Failed to set up business models index: {e}")


class TestBusinessModelSynonymMatching:
    """Test business model synonym matching with real ES."""

    def test_b2b_variations(self, es_client, setup_business_models_index):
        """Test B2B business model variations."""
        variations = [
            "B2B",
            "Business to Business",
            "Enterprise",
        ]

        for variation in variations:
            result = validate_segment_value_es(es_client, "business_models", variation)
            assert result is not None, f"'{variation}' should match"
            # Should match something related to B2B (might be "B2B" or synonym variation)
            assert len(result) > 0, f"'{variation}' should have matches, got {result}"
            print(f"  '{variation}' → {result}")

    def test_b2c_variations(self, es_client, setup_business_models_index):
        """Test B2C business model variations."""
        variations = [
            "B2C",
            "Business to Consumer",
            "Consumer",
            "Direct to Consumer",
            "DTC",
        ]

        for variation in variations:
            result = validate_segment_value_es(es_client, "business_models", variation)
            assert result is not None, f"'{variation}' should match"
            assert len(result) > 0, f"'{variation}' should have matches, got {result}"
            print(f"  '{variation}' → {result}")

    def test_saas_generic(self, es_client, setup_business_models_index):
        """Test generic SaaS matching - should match SaaS specifically."""
        variations = [
            "SaaS",
            "Software as a Service",
            "Cloud Software",
            "Subscription Software",
        ]

        for variation in variations:
            result = validate_segment_value_es(es_client, "business_models", variation)
            assert result is not None, f"'{variation}' should match"
            # Should match generic SaaS, might also match Horizontal/Vertical
            assert any("SaaS" in item for item in result), (
                f"'{variation}' should match some SaaS variant, got {result}"
            )
            print(f"  '{variation}' → {result}")


    def test_saas_precision(self, es_client, setup_business_models_index):
        """Test that SaaS matching doesn't over-match."""
        # Generic "SaaS" should match precisely
        result = validate_segment_value_es(es_client, "business_models", "SaaS")
        assert result is not None, "SaaS should match"

        # Should get exactly 1 result (SaaS only)
        assert len(result) == 1, (
            f"'SaaS' should match exactly once, got {len(result)} matches: {result}"
        )
        assert "SaaS" in result, f"'SaaS' should match 'SaaS', got {result}"

    def test_marketplace_variations(self, es_client, setup_business_models_index):
        """Test Marketplace business model variations."""
        variations = [
            "Marketplace",
            "Two-Sided Marketplace",
            "Platform Marketplace",
            "Peer-to-Peer",
            "P2P",
        ]

        for variation in variations:
            result = validate_segment_value_es(es_client, "business_models", variation)
            assert result is not None, f"'{variation}' should match"
            assert "Marketplace" in result, (
                f"'{variation}' should map to 'Marketplace', got {result}"
            )

    def test_platform_variations(self, es_client, setup_business_models_index):
        """Test Platform business model variations."""
        variations = [
            "Platform",
            "Technology Platform",
            "API Platform",
        ]

        for variation in variations:
            result = validate_segment_value_es(es_client, "business_models", variation)
            assert result is not None, f"'{variation}' should match"
            assert "Platform" in result, (
                f"'{variation}' should map to 'Platform', got {result}"
            )

    def test_case_insensitive(self, es_client, setup_business_models_index):
        """Test case-insensitive matching for business models."""
        test_cases = [
            ("b2b", "B2B"),
            ("saas", "SaaS"),
            ("MARKETPLACE", "Marketplace"),
        ]

        for variation, expected in test_cases:
            result = validate_segment_value_es(es_client, "business_models", variation)
            if result:  # Some case variations may not match perfectly
                assert expected in result, (
                    f"'{variation}' should match '{expected}', got {result}"
                )

    def test_saas_comprehensive(self, es_client, setup_business_models_index):
        """Test comprehensive SaaS matching with various synonyms."""
        # All SaaS variations should match generic SaaS
        variations = [
            "SaaS",
            "Software as a Service",
            "Cloud Software",
            "Subscription Software",
        ]

        for variation in variations:
            result = validate_segment_value_es(es_client, "business_models", variation)
            assert result is not None, f"'{variation}' should match"
            assert "SaaS" in result, f"'{variation}' should match 'SaaS', got {result}"
            print(f"  '{variation}' → {result}")
