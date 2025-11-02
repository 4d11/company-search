"""
Tests for search logic.
"""
from unittest.mock import Mock, patch, MagicMock

import pytest

from backend.db.database import Company, Location, Industry, TargetMarket, FundingStage
from backend.logic.search import search_companies_with_extraction
from backend.models.filters import (
    QueryFilters,
    SegmentFilter,
    FilterRule,
    FilterType,
    OperatorType,
    LogicType,
)


class TestSearchCompaniesWithExtraction:
    """Test suite for search_companies_with_extraction function."""

    @pytest.fixture
    def mock_companies(self):
        """Create mock companies for testing."""
        # Company 1: AI startup
        company1 = Mock(spec=Company)
        company1.id = 1
        company1.company_name = "TestCo AI"
        company1.description = "AI-powered analytics platform"
        company1.employee_count = 25
        company1.funding_amount = 5000000

        mock_location1 = Mock()
        mock_location1.city = "San Francisco"
        company1.location = mock_location1

        mock_stage1 = Mock()
        mock_stage1.name = "Series A"
        company1.funding_stage = mock_stage1

        mock_industry1 = Mock()
        mock_industry1.name = "AI/ML"
        company1.industries = [mock_industry1]

        mock_target1 = Mock()
        mock_target1.name = "Enterprise"
        company1.target_markets = [mock_target1]

        # Company 2: FinTech startup
        company2 = Mock(spec=Company)
        company2.id = 2
        company2.company_name = "FinTech Solutions"
        company2.description = "Financial data platform"
        company2.employee_count = 10
        company2.funding_amount = 1000000

        mock_location2 = Mock()
        mock_location2.city = "New York"
        company2.location = mock_location2

        mock_stage2 = Mock()
        mock_stage2.name = "Seed"
        company2.funding_stage = mock_stage2

        mock_industry2 = Mock()
        mock_industry2.name = "FinTech"
        company2.industries = [mock_industry2]

        mock_target2 = Mock()
        mock_target2.name = "SMB"
        company2.target_markets = [mock_target2]

        return [company1, company2]

    @patch('backend.logic.search.get_query_classifier')
    @patch('backend.logic.search.extract_query_filters')
    @patch('backend.logic.search.search_companies_with_filters')
    @patch('backend.logic.search.batch_generate_explanations')
    @patch('backend.logic.search.rewrite_query_for_search')
    def test_explicit_search_query(
        self,
        mock_rewrite,
        mock_batch_explain,
        mock_es_search,
        mock_extract,
        mock_classifier_func,
        mock_companies
    ):
        """Test explicit search query flow."""
        # Mock classifier
        mock_classifier = Mock()
        mock_classification = Mock()
        mock_classification.classification = "explicit_search"
        mock_classification.is_conceptual = False
        mock_classifier.classify.return_value = mock_classification
        mock_classifier_func.return_value = mock_classifier

        # Mock filter extraction
        extracted_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="AI/ML")]
                )
            ]
        )
        mock_extract.return_value = extracted_filters

        # Mock query rewriting
        mock_rewrite.return_value = "AI machine learning companies"

        # Mock ES search results
        mock_es_search.return_value = [
            {"_id": "1", "_score": 0.9},
            {"_id": "2", "_score": 0.7}
        ]

        # Mock database session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_companies
        mock_db.query.return_value = mock_query

        # Mock batch explanations
        mock_batch_explain.return_value = {
            1: "TestCo AI provides AI-powered analytics.",
            2: "FinTech Solutions offers financial data services."
        }

        # Run search
        results, applied_filters, thesis_context = search_companies_with_extraction(
            query_text="AI companies",
            db=mock_db,
            user_filters=None,
            excluded_values=[],
            size=10
        )

        # Verify results
        assert len(results) == 2
        assert results[0][0].id == 1  # Company 1
        assert results[0][1] == "TestCo AI provides AI-powered analytics."
        assert thesis_context is None  # No thesis for explicit search

        # Verify classifier was called
        mock_classifier.classify.assert_called_once_with("AI companies")

        # Verify filter extraction
        mock_extract.assert_called_once()

        # Verify ES search
        mock_es_search.assert_called_once()

        # Verify explanations were generated
        mock_batch_explain.assert_called_once()

    @patch('backend.logic.search.get_query_classifier')
    @patch('backend.logic.search.analyze_portfolio_for_complementary_thesis')
    @patch('backend.logic.search.extract_query_filters')
    @patch('backend.logic.search.search_companies_with_filters')
    @patch('backend.logic.search.batch_generate_explanations')
    def test_portfolio_analysis_query(
        self,
        mock_batch_explain,
        mock_es_search,
        mock_extract,
        mock_portfolio_analysis,
        mock_classifier_func,
        mock_companies
    ):
        """Test portfolio analysis query flow."""
        # Mock classifier
        mock_classifier = Mock()
        mock_classification = Mock()
        mock_classification.classification = "portfolio_analysis"
        mock_classifier.classify.return_value = mock_classification
        mock_classifier_func.return_value = mock_classifier

        # Mock portfolio analysis
        mock_analysis = Mock()
        mock_analysis.portfolio_summary = "Consumer fintech portfolio"
        mock_analysis.themes = ["consumer credit", "AI automation"]
        mock_analysis.gaps = ["B2B infrastructure"]
        mock_analysis.complementary_areas = ["B2B financial APIs"]
        mock_analysis.strategic_reasoning = "Diversify into B2B"
        mock_analysis.expanded_query = "B2B financial infrastructure APIs"
        mock_portfolio_analysis.return_value = mock_analysis

        # Mock filter extraction
        mock_extract.return_value = QueryFilters(logic=LogicType.AND, filters=[])

        # Mock ES search
        mock_es_search.return_value = [{"_id": "1", "_score": 0.9}]

        # Mock database session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_companies[0]]
        mock_db.query.return_value = mock_query

        # Mock batch explanations
        mock_batch_explain.return_value = {
            1: "Strategic fit explanation"
        }

        # Run search
        results, applied_filters, thesis_context = search_companies_with_extraction(
            query_text="My investments include consumer credit. Suggest additions.",
            db=mock_db,
            user_filters=None,
            excluded_values=[],
            size=10
        )

        # Verify thesis context is returned
        assert thesis_context is not None
        assert thesis_context["type"] == "portfolio"
        assert thesis_context["summary"] == "Consumer fintech portfolio"
        assert "consumer credit" in thesis_context["themes"]
        assert "Diversify into B2B" in thesis_context["strategic_reasoning"]

        # Verify portfolio analysis was called
        mock_portfolio_analysis.assert_called_once()

        # Verify ES search used expanded query
        mock_es_search.assert_called_once()
        call_args = mock_es_search.call_args
        assert call_args.kwargs["query_text"] == "B2B financial infrastructure APIs"

    @patch('backend.logic.search.get_query_classifier')
    @patch('backend.logic.search.extract_query_filters')
    @patch('backend.logic.search.search_companies_with_filters')
    @patch('backend.logic.search.batch_generate_explanations')
    def test_filter_merging(
        self,
        mock_batch_explain,
        mock_es_search,
        mock_extract,
        mock_classifier_func,
        mock_companies
    ):
        """Test that user filters and LLM filters are merged correctly."""
        # Mock classifier
        mock_classifier = Mock()
        mock_classification = Mock()
        mock_classification.classification = "explicit_search"
        mock_classification.is_conceptual = False
        mock_classifier.classify.return_value = mock_classification
        mock_classifier_func.return_value = mock_classifier

        # User provides location filter
        user_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")]
                )
            ]
        )

        # LLM extracts industries filter
        llm_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="AI/ML")]
                )
            ]
        )
        mock_extract.return_value = llm_filters

        # Mock ES search
        mock_es_search.return_value = [{"_id": "1", "_score": 0.9}]

        # Mock database session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_companies[0]]
        mock_db.query.return_value = mock_query

        # Mock batch explanations
        mock_batch_explain.return_value = {1: "Test explanation"}

        # Run search with user filters
        results, applied_filters, thesis_context = search_companies_with_extraction(
            query_text="AI companies",
            db=mock_db,
            user_filters=user_filters,
            excluded_values=[],
            size=10
        )

        # Verify both filters are applied
        assert len(applied_filters.filters) == 2
        filter_segments = [f.segment for f in applied_filters.filters]
        assert "location" in filter_segments
        assert "industries" in filter_segments

    @patch('backend.logic.search.get_query_classifier')
    @patch('backend.logic.search.search_companies_with_filters')
    def test_empty_query(
        self,
        mock_es_search,
        mock_classifier_func
    ):
        """Test search with no query text (filters only)."""
        # Mock ES search with no results
        mock_es_search.return_value = []

        # Mock database session
        mock_db = MagicMock()

        # Run search with empty query
        results, applied_filters, thesis_context = search_companies_with_extraction(
            query_text=None,
            db=mock_db,
            user_filters=None,
            excluded_values=[],
            size=10
        )

        # Verify empty results
        assert len(results) == 0
        assert thesis_context is None

        # Verify classifier was NOT called (no query text)
        mock_classifier_func.return_value.classify.assert_not_called()

    @patch('backend.logic.search.get_query_classifier')
    @patch('backend.logic.search.extract_query_filters')
    @patch('backend.logic.search.search_companies_with_filters')
    @patch('backend.logic.search.batch_generate_explanations')
    @patch('backend.logic.search.explain_result')
    def test_explanation_fallback(
        self,
        mock_explain_result,
        mock_batch_explain,
        mock_es_search,
        mock_extract,
        mock_classifier_func,
        mock_companies
    ):
        """Test that rule-based explanation is used when LLM fails."""
        # Mock classifier
        mock_classifier = Mock()
        mock_classification = Mock()
        mock_classification.classification = "explicit_search"
        mock_classification.is_conceptual = False
        mock_classifier.classify.return_value = mock_classification
        mock_classifier_func.return_value = mock_classifier

        # Mock filter extraction
        mock_extract.return_value = QueryFilters(logic=LogicType.AND, filters=[])

        # Mock ES search
        mock_es_search.return_value = [{"_id": "1", "_score": 0.9}]

        # Mock database session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_companies[0]]
        mock_db.query.return_value = mock_query

        # Mock batch explanations to raise exception
        mock_batch_explain.side_effect = Exception("LLM error")

        # Mock fallback explanation
        mock_explain_result.return_value = "Fallback explanation"

        # Run search
        results, applied_filters, thesis_context = search_companies_with_extraction(
            query_text="AI companies",
            db=mock_db,
            user_filters=None,
            excluded_values=[],
            size=10
        )

        # Verify fallback was used
        assert len(results) == 1
        assert results[0][1] == "Fallback explanation"

        # Verify fallback function was called
        mock_explain_result.assert_called_once()
