"""
Quick test script for the explanation generator.
Run this from the backend directory: poetry run python scripts/test_explanation_generator.py
"""
from unittest.mock import Mock, patch
from backend.llm.explanation_generator import batch_generate_explanations


def test_explanation_generator():
    """Test the explanation generator with mocked LLM."""

    # Create mock companies with proper attributes
    industry_1 = Mock()
    industry_1.name = "AI/ML"
    target_market_1 = Mock()
    target_market_1.name = "Enterprise"
    location_1 = Mock()
    location_1.city = "San Francisco"
    stage_1 = Mock()
    stage_1.name = "Series A"

    mock_company_1 = Mock()
    mock_company_1.id = 1
    mock_company_1.company_name = "TestCo AI"
    mock_company_1.description = "AI-powered analytics platform"
    mock_company_1.industries = [industry_1]
    mock_company_1.target_markets = [target_market_1]
    mock_company_1.business_models = []
    mock_company_1.revenue_models = []
    mock_company_1.location = location_1
    mock_company_1.funding_stage = stage_1
    mock_company_1.funding_amount = 5000000
    mock_company_1.employee_count = 25

    industry_2 = Mock()
    industry_2.name = "FinTech"
    target_market_2 = Mock()
    target_market_2.name = "SMB"
    location_2 = Mock()
    location_2.city = "New York"
    stage_2 = Mock()
    stage_2.name = "Seed"

    mock_company_2 = Mock()
    mock_company_2.id = 2
    mock_company_2.company_name = "FinTech Solutions"
    mock_company_2.description = "Financial data platform"
    mock_company_2.industries = [industry_2]
    mock_company_2.target_markets = [target_market_2]
    mock_company_2.business_models = []
    mock_company_2.revenue_models = []
    mock_company_2.location = location_2
    mock_company_2.funding_stage = stage_2
    mock_company_2.funding_amount = 1000000
    mock_company_2.employee_count = 10

    companies = [mock_company_1, mock_company_2]
    query = "AI and fintech companies"

    # Mock LLM response (natural explanations without rule-based format)
    mock_llm_response = [
        {
            "company_id": 1,
            "explanation": "TestCo AI provides AI-powered analytics for enterprises, focusing on machine learning capabilities to drive data-driven decisions. Based in San Francisco's tech hub, they serve Fortune 500 clients across multiple industries."
        },
        {
            "company_id": 2,
            "explanation": "FinTech Solutions offers a financial data platform designed specifically for SMBs, combining real-time analytics with automated reporting. Their New York-based team focuses on early-stage growth companies in the financial services sector."
        }
    ]

    # Test with mocked LLM client
    with patch('backend.llm.explanation_generator.get_llm_client') as mock_get_client:
        mock_client = Mock()
        mock_client.generate_raw.return_value = mock_llm_response
        mock_get_client.return_value = mock_client

        # Run the function (disable cache for testing)
        result = batch_generate_explanations(
            companies=companies,
            query=query,
            applied_filters=None,
            use_cache=False
        )

        # Verify results
        print("=" * 80)
        print("EXPLANATION GENERATOR TEST")
        print("=" * 80)
        print()

        success = True

        # Check that we got results for both companies
        if len(result) != 2:
            print(f"✗ Expected 2 explanations, got {len(result)}")
            success = False
        else:
            print(f"✓ Generated {len(result)} explanations")

        # Check company 1
        if 1 in result:
            print(f"✓ Explanation for company 1: {result[1][:80]}...")

            # Check that it doesn't contain rule-based format phrases
            bad_phrases = ["Matched filters:", "Matches keywords:", "Good relevance", "High relevance"]
            if any(phrase in result[1] for phrase in bad_phrases):
                print(f"  ✗ WARNING: Contains rule-based format phrases")
                success = False
            else:
                print(f"  ✓ Natural language format (no rule-based phrases)")
        else:
            print("✗ Missing explanation for company 1")
            success = False

        # Check company 2
        if 2 in result:
            print(f"✓ Explanation for company 2: {result[2][:80]}...")

            # Check that it doesn't contain rule-based format phrases
            bad_phrases = ["Matched filters:", "Matches keywords:", "Good relevance", "High relevance"]
            if any(phrase in result[2] for phrase in bad_phrases):
                print(f"  ✗ WARNING: Contains rule-based format phrases")
                success = False
            else:
                print(f"  ✓ Natural language format (no rule-based phrases)")
        else:
            print("✗ Missing explanation for company 2")
            success = False

        # Verify LLM client was called correctly
        if mock_client.generate_raw.called:
            call_args = mock_client.generate_raw.call_args
            if 'system_message' in call_args.kwargs and 'user_message' in call_args.kwargs:
                print("✓ LLM client called with correct parameters (system_message, user_message)")

                # Check that user_message contains the query
                user_message = call_args.kwargs['user_message']
                if query in user_message:
                    print(f"✓ Query '{query}' included in prompt")
                else:
                    print(f"✗ Query not found in prompt")
                    success = False

                # Check that company data is in the prompt
                if "TestCo AI" in user_message and "FinTech Solutions" in user_message:
                    print("✓ Company data included in prompt")
                else:
                    print("✗ Company data not found in prompt")
                    success = False

                # Check that prompt includes instructions to avoid rule-based format
                if "DO NOT use phrases like" in user_message and "Matched filters" in user_message:
                    print("✓ Prompt includes instructions to avoid rule-based format")
                else:
                    print("✗ Prompt missing instructions to avoid rule-based format")
                    success = False
            else:
                print("✗ LLM client called with incorrect parameters")
                success = False
        else:
            print("✗ LLM client was not called")
            success = False

        print()
        print("=" * 80)
        if success:
            print("✓ ALL TESTS PASSED")
        else:
            print("✗ SOME TESTS FAILED")
        print("=" * 80)

        return success


if __name__ == "__main__":
    test_explanation_generator()
