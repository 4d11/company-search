"""
Tests for query API routes.
"""
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from backend.db.database import Company, Industry, TargetMarket, Location, FundingStage, BusinessModel, RevenueModel
from backend.models.filters import QueryFilters, FilterType, LogicType, SegmentFilter, FilterRule, OperatorType
from main import app


class TestSubmitQueryEndpoint:
    """Test suite for POST /api/submit-query endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        mock_session = MagicMock()

        # Mock query builder chain
        mock_query = MagicMock()
        mock_query.order_by.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        return mock_session

    @patch('backend.routes.query.search_companies_with_extraction')
    def test_submit_query_with_text_query(self, mock_search, client, mock_db):
        """Test submitting a text query."""
        # Mock company data
        mock_company = Mock(spec=Company)
        mock_company.id = 1
        mock_company.company_name = "TestCo AI"
        mock_company.company_id = 1001
        mock_company.city = "San Francisco"
        mock_company.description = "AI-powered analytics platform"
        mock_company.website_url = "https://testco.ai"
        mock_company.employee_count = 25
        mock_company.funding_amount = 5000000

        # Mock relationships
        mock_location = Mock()
        mock_location.city = "San Francisco"
        mock_company.location = mock_location

        mock_stage = Mock()
        mock_stage.name = "Series A"
        mock_company.funding_stage = mock_stage

        mock_industry = Mock()
        mock_industry.name = "AI/ML"
        mock_company.industries = [mock_industry]

        mock_target_market = Mock()
        mock_target_market.name = "Enterprise"
        mock_company.target_markets = [mock_target_market]

        # Mock search result
        explanation = "TestCo AI provides AI-powered analytics for enterprises."
        mock_filters = QueryFilters(logic=LogicType.AND, filters=[])
        mock_search.return_value = (
            [(mock_company, explanation)],
            mock_filters,
            None  # No thesis context
        )

        # Make request
        with patch('backend.routes.query.get_db', return_value=mock_db):
            response = client.post(
                "/api/submit-query",
                json={"query": "AI companies in SF"}
            )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert len(data["companies"]) == 1
        assert data["companies"][0]["company_name"] == "TestCo AI"
        assert data["companies"][0]["explanation"] == explanation
        assert data["applied_filters"]["logic"] == "AND"
        assert data["thesis_context"] is None

        # Verify search was called correctly
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args.kwargs["query_text"] == "AI companies in SF"
        assert call_args.kwargs["size"] == 15

    @patch('backend.routes.query.search_companies_with_extraction')
    def test_submit_query_without_filters(self, mock_search, client, mock_db):
        """Test submitting a query without filters."""
        mock_company = Mock(spec=Company)
        mock_company.id = 1
        mock_company.company_name = "TestCo"
        mock_company.company_id = 1001
        mock_company.city = None
        mock_company.description = "Test company"
        mock_company.website_url = "https://test.com"
        mock_company.employee_count = 10
        mock_company.funding_amount = 1000000
        mock_company.location = None
        mock_company.funding_stage = None
        mock_company.industries = []
        mock_company.target_markets = []

        # Mock filters
        mock_filters = QueryFilters(logic=LogicType.AND, filters=[])

        mock_search.return_value = (
            [(mock_company, "Test explanation")],
            mock_filters,
            None
        )

        # Make request without filters
        with patch('backend.routes.query.get_db', return_value=mock_db):
            response = client.post(
                "/api/submit-query",
                json={"query": "fintech startups"}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify search was called
        mock_search.assert_called_once()

    @patch('backend.routes.query.search_companies_with_extraction')
    def test_submit_query_with_portfolio_analysis(self, mock_search, client, mock_db):
        """Test portfolio analysis query returns thesis context."""
        mock_company = Mock(spec=Company)
        mock_company.id = 1
        mock_company.company_name = "TestCo"
        mock_company.company_id = 1001
        mock_company.city = None
        mock_company.description = "Test company"
        mock_company.website_url = "https://test.com"
        mock_company.employee_count = 10
        mock_company.funding_amount = 1000000
        mock_company.location = None
        mock_company.funding_stage = None
        mock_company.industries = []
        mock_company.target_markets = []

        # Mock thesis context
        thesis_context = {
            "type": "portfolio",
            "summary": "Consumer fintech focused portfolio",
            "themes": ["consumer credit", "AI automation"],
            "gaps": ["B2B infrastructure"],
            "complementary_areas": ["B2B financial APIs", "enterprise billing"],
            "strategic_reasoning": "Diversify into B2B while leveraging AI expertise"
        }

        mock_filters = QueryFilters(logic=LogicType.AND, filters=[])
        mock_search.return_value = (
            [(mock_company, "Strategic fit explanation")],
            mock_filters,
            thesis_context
        )

        # Make portfolio query
        with patch('backend.routes.query.get_db', return_value=mock_db):
            response = client.post(
                "/api/submit-query",
                json={"query": "My investments include consumer credit and AI tax prep. Suggest additions."}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify thesis context is present
        assert data["thesis_context"] is not None
        assert data["thesis_context"]["type"] == "portfolio"
        assert "consumer credit" in data["thesis_context"]["themes"]
        assert len(data["thesis_context"]["complementary_areas"]) > 0

    @patch('backend.routes.query.search_companies_with_extraction')
    def test_submit_query_empty_query(self, mock_search, client, mock_db):
        """Test submitting query with no text (filters only)."""
        mock_filters = QueryFilters(logic=LogicType.AND, filters=[])
        mock_search.return_value = ([], mock_filters, None)

        with patch('backend.routes.query.get_db', return_value=mock_db):
            response = client.post(
                "/api/submit-query",
                json={"query": None}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify search was called with None query
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args.kwargs["query_text"] is None

    def test_get_filter_options(self, client):
        """Test GET /api/filter-options endpoint."""
        # Mock database objects
        mock_location = Mock()
        mock_location.city = "San Francisco"

        mock_industry1 = Mock()
        mock_industry1.name = "AI & Machine Learning"
        mock_industry2 = Mock()
        mock_industry2.name = "FinTech"

        mock_target = Mock()
        mock_target.name = "Enterprise"

        mock_stage = Mock()
        mock_stage.name = "Series A"

        mock_bm = Mock()
        mock_bm.name = "B2B"

        mock_rm = Mock()
        mock_rm.name = "Subscription"

        # Create mock session
        mock_session = MagicMock()

        # Mock query chains for each entity type
        def mock_query_side_effect(entity):
            mock_query = MagicMock()
            if entity == Location:
                mock_query.order_by.return_value.all.return_value = [mock_location]
            elif entity == Industry:
                mock_query.order_by.return_value.all.return_value = [mock_industry1, mock_industry2]
            elif entity == TargetMarket:
                mock_query.order_by.return_value.all.return_value = [mock_target]
            elif entity == FundingStage:
                mock_query.order_by.return_value.all.return_value = [mock_stage]
            elif entity == BusinessModel:
                mock_query.order_by.return_value.all.return_value = [mock_bm]
            elif entity == RevenueModel:
                mock_query.order_by.return_value.all.return_value = [mock_rm]
            return mock_query

        mock_session.query.side_effect = mock_query_side_effect

        with patch('backend.routes.query.get_db', return_value=mock_session):
            response = client.get("/api/filter-options")

        assert response.status_code == 200
        data = response.json()

        # Verify all filter types are present
        assert "locations" in data
        assert "industries" in data
        assert "target_markets" in data
        assert "stages" in data
        assert "business_models" in data
        assert "revenue_models" in data

        # Verify response structure
        assert isinstance(data["locations"], list)
        assert isinstance(data["industries"], list)
        assert isinstance(data["target_markets"], list)
        assert isinstance(data["stages"], list)

        # Verify test data is present
        assert "San Francisco" in data["locations"]
        assert "AI & Machine Learning" in data["industries"]
        assert "FinTech" in data["industries"]
        assert "Enterprise" in data["target_markets"]
        assert "Series A" in data["stages"]
