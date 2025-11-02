"""
Tests for Elasticsearch operations.
"""
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from backend.db.database import Company, FundingStage, Industry, Location, TargetMarket
from backend.es.operations import (
    bulk_index_companies,
    index_company,
    search_companies_by_vector,
)


class TestIndexCompany:
    """Test suite for index_company function."""

    @patch('backend.es.operations.generate_embedding')
    def test_index_company_basic(self, mock_generate_embedding):
        """Test indexing a company with basic fields."""
        # Mock embedding generation
        mock_generate_embedding.return_value = [0.1] * 1024

        # Create mock company
        company = Company(
            id=1,
            company_id=100,
            company_name="Test Company",
            city="Test City",
            description="A test company",
            website_url="https://test.com",
            website_text="Test website",
            created_at=datetime(2024, 1, 1)
        )

        # Mock Elasticsearch client
        mock_es = MagicMock()

        # Index company
        index_company(mock_es, company)

        # Verify ES index was called
        mock_es.index.assert_called_once()
        call_args = mock_es.index.call_args[1]

        assert call_args["id"] == 1
        assert call_args["document"]["company_name"] == "Test Company"
        assert call_args["document"]["description"] == "A test company"
        assert len(call_args["document"]["description_vector"]) == 1024

    @patch('backend.es.operations.generate_embedding')
    def test_index_company_with_relationships(self, mock_generate_embedding):
        """Test indexing a company with location, industries, and target markets."""
        mock_generate_embedding.return_value = [0.1] * 1024

        # Create related objects
        location = Location(id=1, city="San Francisco")
        industry1 = Industry(id=1, name="SaaS")
        industry2 = Industry(id=2, name="AI/ML")
        market = TargetMarket(id=1, name="SMB")
        stage = FundingStage(id=1, name="Series A", order_index=3)

        company = Company(
            id=1,
            company_id=100,
            company_name="Test Company",
            description="A test company",
            location=location,
            employee_count=50,
            funding_amount=5000000,
            funding_stage=stage
        )
        company.industries = [industry1, industry2]
        company.target_markets = [market]

        mock_es = MagicMock()
        index_company(mock_es, company)

        call_args = mock_es.index.call_args[1]
        doc = call_args["document"]

        assert doc["location"] == "San Francisco"
        assert "SaaS" in doc["industries"]
        assert "AI/ML" in doc["industries"]
        assert "SMB" in doc["target_markets"]
        assert doc["employee_count"] == 50
        assert doc["funding_amount"] == 5000000
        assert doc["funding_stage"] == "Series A"


class TestBulkIndexCompanies:
    """Test suite for bulk_index_companies function."""

    @patch('backend.es.operations.generate_embeddings_batch')
    @patch('backend.es.operations.bulk')
    def test_bulk_index_companies(self, mock_bulk, mock_generate_embeddings_batch):
        """Test bulk indexing multiple companies."""
        # Mock embedding generation
        mock_generate_embeddings_batch.return_value = [
            [0.1] * 1024,
            [0.2] * 1024,
            [0.3] * 1024
        ]

        # Create test companies
        companies = [
            Company(id=1, company_id=100, company_name="Company 1", description="Desc 1"),
            Company(id=2, company_id=101, company_name="Company 2", description="Desc 2"),
            Company(id=3, company_id=102, company_name="Company 3", description="Desc 3"),
        ]

        mock_es = MagicMock()
        bulk_index_companies(mock_es, companies)

        # Verify bulk was called
        mock_bulk.assert_called_once()
        call_args = mock_bulk.call_args[0]

        # Check that actions were created for all companies
        actions = list(call_args[1])
        assert len(actions) == 3

        # Verify first action structure
        assert actions[0]["_id"] == 1
        assert actions[0]["_source"]["company_name"] == "Company 1"


class TestSearchCompaniesByVector:
    """Test suite for search_companies_by_vector function."""

    @patch('backend.es.operations.generate_embedding')
    def test_search_no_filters(self, mock_generate_embedding):
        """Test search without any filters uses kNN."""
        mock_generate_embedding.return_value = [0.1] * 1024

        mock_es = MagicMock()
        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {"_id": "1", "_source": {"company_name": "Company 1"}, "_score": 0.9}
                ]
            }
        }

        result = search_companies_by_vector(
            es=mock_es,
            query_text="test query",
            size=10
        )

        # Verify search was called
        mock_es.search.assert_called_once()
        call_args = mock_es.search.call_args[1]

        # Should use kNN when no filters
        assert "knn" in call_args["body"]
        assert "query" not in call_args["body"]

    @patch('backend.es.operations.generate_embedding')
    def test_search_with_location_filter(self, mock_generate_embedding):
        """Test search with location filter uses script_score."""
        mock_generate_embedding.return_value = [0.1] * 1024

        mock_es = MagicMock()
        mock_es.search.return_value = {"hits": {"hits": []}}

        search_companies_by_vector(
            es=mock_es,
            query_text="test query",
            location="San Francisco"
        )

        call_args = mock_es.search.call_args[1]

        # Should use script_score with filters
        assert "query" in call_args["body"]
        assert "script_score" in call_args["body"]["query"]
        assert "knn" not in call_args["body"]

    @patch('backend.es.operations.generate_embedding')
    def test_search_with_industries_filter(self, mock_generate_embedding):
        """Test search with industries filter."""
        mock_generate_embedding.return_value = [0.1] * 1024

        mock_es = MagicMock()
        mock_es.search.return_value = {"hits": {"hits": []}}

        search_companies_by_vector(
            es=mock_es,
            query_text="test query",
            industries=["SaaS", "AI/ML"]
        )

        call_args = mock_es.search.call_args[1]

        # Should use script_score with filters
        assert "query" in call_args["body"]
        assert "script_score" in call_args["body"]["query"]

    @patch('backend.es.operations.generate_embedding')
    def test_search_with_employee_range(self, mock_generate_embedding):
        """Test search with employee count range."""
        mock_generate_embedding.return_value = [0.1] * 1024

        mock_es = MagicMock()
        mock_es.search.return_value = {"hits": {"hits": []}}

        search_companies_by_vector(
            es=mock_es,
            query_text="test query",
            min_employees=10,
            max_employees=100
        )

        call_args = mock_es.search.call_args[1]

        # Should use script_score with filters
        assert "query" in call_args["body"]
        assert "script_score" in call_args["body"]["query"]


    @patch('backend.es.operations.generate_embedding')
    def test_search_with_funding_range(self, mock_generate_embedding):
        """Test search with funding amount range."""
        mock_generate_embedding.return_value = [0.1] * 1024

        mock_es = MagicMock()
        mock_es.search.return_value = {"hits": {"hits": []}}

        search_companies_by_vector(
            es=mock_es,
            query_text="test query",
            min_funding=1000000,
            max_funding=10000000
        )

        call_args = mock_es.search.call_args[1]

        # Should use script_score with filters
        assert "query" in call_args["body"]
        assert "script_score" in call_args["body"]["query"]

    @patch('backend.es.operations.generate_embedding')
    def test_search_result_parsing(self, mock_generate_embedding):
        """Test that search results are parsed correctly."""
        mock_generate_embedding.return_value = [0.1] * 1024

        mock_es = MagicMock()
        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": "1",
                        "_source": {
                            "company_name": "Company 1",
                            "description": "Test description"
                        },
                        "_score": 0.95
                    },
                    {
                        "_id": "2",
                        "_source": {
                            "company_name": "Company 2",
                            "description": "Another description"
                        },
                        "_score": 0.85
                    }
                ]
            }
        }

        result = search_companies_by_vector(
            es=mock_es,
            query_text="test query",
            size=10
        )

        assert len(result) == 2
        assert result[0]["company_name"] == "Company 1"
        assert result[0]["_score"] == 0.95
        assert result[1]["company_name"] == "Company 2"
        assert result[1]["_score"] == 0.85
