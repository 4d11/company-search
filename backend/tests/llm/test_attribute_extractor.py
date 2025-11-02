"""
Tests for attribute extraction.
"""
from unittest.mock import MagicMock, patch

import pytest

from backend.db.database import Industry, Location, TargetMarket
from backend.llm.attribute_extractor import (
    extract_company_attributes,
    get_supported_attributes,
)


class TestGetSupportedAttributes:
    """Test suite for get_supported_attributes."""

    def test_get_supported_attributes(self, temp_db):
        """Test retrieving supported attributes from database."""
        # Add test data
        temp_db.add(Location(city="San Francisco"))
        temp_db.add(Location(city="New York"))
        temp_db.add(Industry(name="SaaS"))
        temp_db.add(Industry(name="AI/ML"))
        temp_db.add(TargetMarket(name="SMB"))
        temp_db.add(TargetMarket(name="Enterprise"))
        temp_db.commit()

        # Get supported attributes
        supported = get_supported_attributes(temp_db)

        assert "San Francisco" in supported["locations"]
        assert "New York" in supported["locations"]
        assert "SaaS" in supported["industries"]
        assert "AI/ML" in supported["industries"]
        assert "SMB" in supported["target_markets"]
        assert "Enterprise" in supported["target_markets"]

    def test_empty_database(self, temp_db):
        """Test with empty database."""
        supported = get_supported_attributes(temp_db)

        assert supported["locations"] == []
        assert supported["industries"] == []
        assert supported["target_markets"] == []


class TestExtractCompanyAttributes:
    """Test suite for extract_company_attributes."""

    @patch('backend.llm.attribute_extractor.get_llm_client')
    @patch('backend.llm.attribute_extractor.settings')
    def test_successful_extraction(self, mock_settings, mock_get_llm_client, temp_db):
        """Test successful attribute extraction."""
        # Disable cache for this test
        mock_settings.use_llm_cache = False

        # Setup test data
        temp_db.add(Location(city="San Francisco"))
        temp_db.add(Industry(name="SaaS"))
        temp_db.add(Industry(name="AI/ML"))
        temp_db.add(TargetMarket(name="SMB"))
        temp_db.commit()

        # Mock LLM response
        mock_get_llm_client.return_value.generate.return_value = {
            "location": "San Francisco",
            "industries": ["SaaS", "AI/ML"],
            "target_markets": ["SMB"]
        }

        # Extract attributes
        result = extract_company_attributes(
            company_name="Test Company",
            description="A SaaS company",
            website_text="We build software",
            db=temp_db
        )

        assert result["location"] == "San Francisco"
        assert "SaaS" in result["industries"]
        assert "AI/ML" in result["industries"]
        assert "SMB" in result["target_markets"]

    @patch('backend.llm.attribute_extractor.get_llm_client')
    @patch('backend.llm.attribute_extractor.settings')
    def test_validation_filters_invalid_values(self, mock_settings, mock_get_llm_client, temp_db):
        """Test that validation filters out invalid attribute values."""
        # Disable cache
        mock_settings.use_llm_cache = False

        # Setup test data (only some values)
        temp_db.add(Location(city="San Francisco"))
        temp_db.add(Industry(name="SaaS"))
        temp_db.commit()

        # Mock LLM response with some invalid values
        mock_get_llm_client.return_value.generate.return_value = {
            "location": "Invalid City",  # Not in database
            "industries": ["SaaS", "InvalidIndustry"],  # One valid, one invalid
            "target_markets": ["InvalidMarket"]  # Invalid
        }

        result = extract_company_attributes(
            company_name="Test Company",
            description="A company",
            website_text="",
            db=temp_db
        )

        # Invalid location should be None
        assert result["location"] is None
        # Only valid industry should remain
        assert result["industries"] == ["SaaS"]
        # Invalid market should be filtered out
        assert result["target_markets"] == []

    @patch('backend.llm.attribute_extractor.get_llm_client')
    @patch('backend.llm.attribute_extractor.settings')
    def test_null_location(self, mock_settings, mock_get_llm_client, temp_db):
        """Test handling of null location."""
        mock_settings.use_llm_cache = False

        temp_db.add(Industry(name="SaaS"))
        temp_db.add(TargetMarket(name="SMB"))
        temp_db.commit()

        mock_get_llm_client.return_value.generate.return_value = {
            "location": None,
            "industries": ["SaaS"],
            "target_markets": ["SMB"]
        }

        result = extract_company_attributes(
            company_name="Test Company",
            description="A company",
            website_text="",
            db=temp_db
        )

        assert result["location"] is None
        assert result["industries"] == ["SaaS"]

    @patch('backend.llm.attribute_extractor.get_llm_client')
    @patch('backend.llm.attribute_extractor.settings')
    def test_max_industries_capped(self, mock_settings, mock_get_llm_client, temp_db):
        """Test that industries are capped at 3."""
        mock_settings.use_llm_cache = False

        # Add many industries
        for name in ["SaaS", "AI/ML", "FinTech", "HealthTech", "EdTech"]:
            temp_db.add(Industry(name=name))
        temp_db.commit()

        # LLM returns more than 3
        mock_get_llm_client.return_value.generate.return_value = {
            "location": None,
            "industries": ["SaaS", "AI/ML", "FinTech", "HealthTech", "EdTech"],
            "target_markets": []
        }

        result = extract_company_attributes(
            company_name="Test Company",
            description="A company",
            website_text="",
            db=temp_db
        )

        # Should be capped at 3
        assert len(result["industries"]) == 3

    @patch('backend.llm.attribute_extractor.get_llm_client')
    @patch('backend.llm.attribute_extractor.settings')
    def test_max_target_markets_capped(self, mock_settings, mock_get_llm_client, temp_db):
        """Test that target markets are capped at 2."""
        mock_settings.use_llm_cache = False

        # Add many target markets
        for name in ["SMB", "Enterprise", "Mid-Market"]:
            temp_db.add(TargetMarket(name=name))
        temp_db.commit()

        # LLM returns more than 2
        mock_get_llm_client.return_value.generate.return_value = {
            "location": None,
            "industries": [],
            "target_markets": ["SMB", "Enterprise", "Mid-Market"]
        }

        result = extract_company_attributes(
            company_name="Test Company",
            description="A company",
            website_text="",
            db=temp_db
        )

        # Should be capped at 2
        assert len(result["target_markets"]) == 2

    @patch('backend.llm.attribute_extractor.get_llm_client')
    @patch('backend.llm.attribute_extractor.settings')
    def test_extraction_error_handling(self, mock_settings, mock_get_llm_client, temp_db):
        """Test that errors are handled gracefully."""
        mock_settings.use_llm_cache = False

        # Mock LLM to raise an error
        mock_get_llm_client.return_value.generate.side_effect = Exception("LLM error")

        result = extract_company_attributes(
            company_name="Test Company",
            description="A company",
            website_text="",
            db=temp_db
        )

        # Should return empty result on error
        assert result["location"] is None
        assert result["industries"] == []
        assert result["target_markets"] == []

    @patch('backend.llm.attribute_extractor.extraction_cache')
    @patch('backend.llm.attribute_extractor.get_llm_client')
    @patch('backend.llm.attribute_extractor.settings')
    def test_cache_hit(self, mock_settings, mock_get_llm_client, mock_cache, temp_db):
        """Test that cache is used when available."""
        mock_settings.use_llm_cache = True

        # Mock cache hit
        cached_result = {
            "location": "San Francisco",
            "industries": ["SaaS"],
            "target_markets": ["SMB"]
        }
        mock_cache.get.return_value = cached_result

        result = extract_company_attributes(
            company_name="Test Company",
            description="A company",
            website_text="",
            db=temp_db
        )

        # Should return cached result
        assert result == cached_result
        # LLM should not be called
        mock_get_llm_client.return_value.generate.assert_not_called()

    @patch('backend.llm.attribute_extractor.extraction_cache')
    @patch('backend.llm.attribute_extractor.get_llm_client')
    @patch('backend.llm.attribute_extractor.settings')
    def test_cache_miss_stores_result(self, mock_settings, mock_get_llm_client, mock_cache, temp_db):
        """Test that results are cached on cache miss."""
        mock_settings.use_llm_cache = True

        # Mock cache miss
        mock_cache.get.return_value = None

        # Setup database
        temp_db.add(Location(city="San Francisco"))
        temp_db.add(Industry(name="SaaS"))
        temp_db.add(TargetMarket(name="SMB"))
        temp_db.commit()

        # Mock LLM response
        llm_result = {
            "location": "San Francisco",
            "industries": ["SaaS"],
            "target_markets": ["SMB"]
        }
        mock_get_llm_client.return_value.generate.return_value = llm_result

        result = extract_company_attributes(
            company_name="Test Company",
            description="A company",
            website_text="",
            db=temp_db
        )

        # LLM should be called
        mock_get_llm_client.return_value.generate.assert_called_once()
        # Result should be cached
        mock_cache.set.assert_called_once()
