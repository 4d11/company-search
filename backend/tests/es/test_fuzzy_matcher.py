"""
Tests for Elasticsearch fuzzy matcher.
"""
from unittest.mock import MagicMock

import pytest

from backend.es.fuzzy_matcher import (
    fuzzy_match_value,
    get_unique_segment_values,
    validate_segment_value_es,
)


class TestGetUniqueSegmentValues:
    """Test getting unique segment values from ES index."""

    def test_get_unique_locations(self):
        """Test getting unique location values."""
        # Mock ES client
        es_client = MagicMock()
        es_client.search.return_value = {
            "aggregations": {
                "unique_values": {
                    "buckets": [
                        {"key": "San Francisco", "doc_count": 10},
                        {"key": "New York", "doc_count": 8},
                        {"key": "Boston", "doc_count": 5},
                    ]
                }
            }
        }

        result = get_unique_segment_values(es_client, "location")

        assert result == ["San Francisco", "New York", "Boston"]
        # Verify ES query
        call_args = es_client.search.call_args
        assert call_args[1]["index"] == "companies"
        assert call_args[1]["body"]["size"] == 0
        assert "aggs" in call_args[1]["body"]

    def test_get_unique_industries(self):
        """Test getting unique industry values."""
        es_client = MagicMock()
        es_client.search.return_value = {
            "aggregations": {
                "unique_values": {
                    "buckets": [
                        {"key": "AI/ML", "doc_count": 15},
                        {"key": "FinTech", "doc_count": 12},
                    ]
                }
            }
        }

        result = get_unique_segment_values(es_client, "industries")

        assert result == ["AI/ML", "FinTech"]

    def test_error_handling(self):
        """Test error handling when ES query fails."""
        es_client = MagicMock()
        es_client.search.side_effect = Exception("ES connection error")

        result = get_unique_segment_values(es_client, "location")

        assert result == []


class TestFuzzyMatchValue:
    """Test fuzzy matching values using ES."""

    def test_exact_match(self):
        """Test exact match returns the value in a list."""
        es_client = MagicMock()
        es_client.msearch.return_value = {
            "responses": [
                {
                    "hits": {
                        "hits": [
                            {
                                "_id": "1",
                                "_score": 3.5,
                                "_source": {"name": "San Francisco"},
                            }
                        ]
                    }
                }
            ]
        }

        result = fuzzy_match_value(es_client, "location", "San Francisco")

        assert result == ["San Francisco"]

    def test_fuzzy_match_abbreviation(self):
        """Test fuzzy match with abbreviation."""
        es_client = MagicMock()
        es_client.msearch.return_value = {
            "responses": [
                {
                    "hits": {
                        "hits": [
                            {
                                "_id": "1",
                                "_score": 2.8,  # Good match
                                "_source": {"name": "San Francisco"},
                            }
                        ]
                    }
                }
            ]
        }

        result = fuzzy_match_value(es_client, "location", "SF", threshold=0.80)

        assert result == ["San Francisco"]

    def test_fuzzy_match_typo(self):
        """Test fuzzy match handles typos."""
        es_client = MagicMock()
        es_client.msearch.return_value = {
            "responses": [
                {
                    "hits": {
                        "hits": [
                            {
                                "_id": "1",
                                "_score": 3.2,
                                "_source": {"name": "FinTech"},
                            }
                        ]
                    }
                }
            ]
        }

        result = fuzzy_match_value(es_client, "industries", "fintech")

        assert result == ["FinTech"]

    def test_no_match_below_threshold(self):
        """Test no match when quality score is below threshold."""
        es_client = MagicMock()
        es_client.msearch.return_value = {
            "responses": [
                {
                    "hits": {
                        "hits": [
                            {
                                "_id": "1",
                                "_score": 5.0,  # Best match (San Diego)
                                "_source": {"name": "San Diego"},
                            },
                            {
                                "_id": "2",
                                "_score": 0.8,  # Low score relative to max (Tokyo)
                                "_source": {"name": "Tokyo"},
                            }
                        ]
                    }
                }
            ]
        }

        result = fuzzy_match_value(
            es_client, "location", "San Francisco", threshold=0.80
        )

        # Should only include San Diego (normalized score 1.0), not Tokyo (normalized 0.16)
        assert result == ["San Diego"]

    def test_no_results(self):
        """Test when ES returns no results."""
        es_client = MagicMock()
        es_client.msearch.return_value = {
            "responses": [{"hits": {"hits": []}}]
        }

        result = fuzzy_match_value(es_client, "location", "Nonexistent City")

        assert result is None

    def test_uses_fuzziness_in_query(self):
        """Verify ES query uses fuzziness parameter."""
        es_client = MagicMock()
        es_client.msearch.return_value = {
            "responses": [
                {
                    "hits": {
                        "hits": [
                            {
                                "_id": "1",
                                "_score": 3.0,
                                "_source": {"name": "New York"},
                            }
                        ]
                    }
                }
            ]
        }

        fuzzy_match_value(es_client, "location", "NYC")

        # Verify msearch was called with proper structure
        call_args = es_client.msearch.call_args
        msearch_body = call_args[1]["body"]
        # msearch body is a list of alternating index and query dicts
        assert len(msearch_body) >= 2
        query_body = msearch_body[1]  # Second item is the query
        assert "query" in query_body
        assert "bool" in query_body["query"]  # Uses bool query with multiple strategies

    def test_error_handling(self):
        """Test error handling when ES query fails."""
        es_client = MagicMock()
        es_client.msearch.side_effect = Exception("ES error")

        result = fuzzy_match_value(es_client, "location", "San Francisco")

        assert result is None


class TestValidateSegmentValueES:
    """Test the main validation entry point."""

    def test_fuzzy_segment_uses_fuzzy_matching(self):
        """Test fuzzy segments use ES fuzzy matching."""
        es_client = MagicMock()
        es_client.msearch.return_value = {
            "responses": [
                {
                    "hits": {
                        "hits": [
                            {
                                "_id": "1",
                                "_score": 3.0,
                                "_source": {"name": "San Francisco"},
                            }
                        ]
                    }
                }
            ]
        }

        result = validate_segment_value_es(es_client, "location", "SF")

        assert result == ["San Francisco"]
        # Verify ES was called
        assert es_client.msearch.called

    def test_non_fuzzy_segment_returns_as_is(self):
        """Test non-fuzzy segments return value as-is in a list."""
        es_client = MagicMock()

        # funding_stage is not in FUZZY_SEGMENTS
        result = validate_segment_value_es(es_client, "funding_stage", "Series A")

        assert result == ["Series A"]
        # Verify ES was NOT called (no msearch for non-fuzzy segments)
        assert not es_client.msearch.called

    def test_employee_count_returns_as_is(self):
        """Test numeric segments return as-is in a list."""
        es_client = MagicMock()

        result = validate_segment_value_es(es_client, "employee_count", "50")

        assert result == ["50"]
        assert not es_client.msearch.called
